"""Controller-only, process-shared serialization and rolling quota accounting."""
import fcntl
import json
import time
from contextlib import contextmanager
from pathlib import Path


class Pacer:
    def __init__(self, path, limits, interval=3, clock=time.time, sleep=time.sleep):
        self.path = Path(path)
        self.limits, self.interval = limits, max(3, interval)
        self.clock, self.sleep = clock, sleep

    @contextmanager
    def slot(self, model, reservation, deadline_seconds):
        # Hold the lock throughout the upstream response, across processes/models.
        with self.path.with_suffix('.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            state = json.loads(self.path.read_text()) if self.path.exists() else {'events': []}
            if state.get('blocked'):
                raise ValueError('Shared pacing state blocked after unknown usage/provider error')
            if reservation > self.limits[model]:
                raise ValueError('Request reservation exceeds rolling token allowance')
            until = self.clock() + deadline_seconds
            while True:
                now = self.clock()
                state['events'] = [e for e in state['events'] if now - e['start'] < 60]
                wait = max(0, state.get('last_start', 0) + self.interval - now)
                events = [e for e in state['events'] if e['model'] == model]
                if sum(e['tokens'] for e in events) + reservation > self.limits[model]:
                    wait = max(wait, min(e['start'] for e in events) + 60 - now)
                if wait <= 0:
                    break
                if now + wait >= until:
                    raise ValueError('Pacing wait would exceed session lifetime')
                self.sleep(min(wait, 30))
            event = {'model': model, 'start': self.clock(), 'tokens': reservation,
                     'usage': None, 'reservation_units': reservation}
            state['last_start'] = event['start']
            state['events'].append(event)
            # Unknown interrupted requests block subsequent calls, rather than disappear.
            state['blocked'] = True
            self.path.write_text(json.dumps(state, indent=2) + '\n')
            try:
                yield event
            finally:
                if event['usage'] is not None:
                    event['tokens'] = event['usage']['total_tokens']
                    state['blocked'] = False
                self.path.write_text(json.dumps(state, indent=2) + '\n')
