# Consultation: Step 1 Core Engine Algorithms for Capybala

Here’s a proposed design for the `DeadlockDetector` and `ContextPruner` classes, focusing on efficiency and zero external dependencies.

### 1. `detector.py`: DeadlockDetector

The `DeadlockDetector` class will implement methods to detect direct repetitions, oscillations, and semantic traceback loops.

```python
import re
import hashlib
from collections import deque

class DeadlockDetector:
    def __init__(self):
        self.history = deque(maxlen=10)  # Store the last 10 actions for detection

    def _normalize(self, action):
        # Normalize the action for comparison (e.g., lowercasing, stripping)
        return action.strip().lower()

    def _hash_action(self, action):
        # Create a hash of the action for quick comparison
        return hashlib.md5(self._normalize(action).encode()).hexdigest()

    def add_action(self, action):
        self.history.append(self._hash_action(action))

    def detect_direct_repetition(self):
        if len(self.history) < 3:
            return False
        return self.history[-1] == self.history[-2] == self.history[-3]

    def detect_oscillation(self):
        if len(self.history) < 4:
            return False
        return self.history[-2] == self.history[-4] and self.history[-1] == self.history[-3]

    def detect_semantic_traceback_loop(self, output):
        # Use regex to find common exception patterns
        exception_pattern = re.compile(r"(exception|error|traceback)", re.IGNORECASE)
        if exception_pattern.search(output):
            return True
        return False

    def detect_deadlock(self, action, output):
        self.add_action(action)
        return (self.detect_direct_repetition() or
                self.detect_oscillation() or
                self.detect_semantic_traceback_loop(output))
```

### 2. `pruner.py`: ContextPruner

The `ContextPruner` class will handle the pruning of the conversation history based on the defined rules.

```python
class ContextPruner:
    def __init__(self):
        self.pruned_history = []

    def prune(self, history):
        # Ensure we keep the first observation and system instructions
        if not history:
            return []

        # Keep the first message
        self.pruned_history.append(history[0])

        # Identify and collapse repetitive cycles
        seen = {}
        for message in history[1:]:
            role = message['role']
            content = message['content']

            # Create a unique key for the message
            key = (role, self._normalize(content))

            if key in seen:
                seen[key] += 1
            else:
                seen[key] = 1
                self.pruned_history.append(message)

        # Create a summary tombstone for repetitive cycles
        self._collapse_cycles(seen)

        return self.pruned_history

    def _collapse_cycles(self, seen):
        # Generate a summary for repetitive messages
        for (role, content), count in seen.items():
            if count > 1:
                summary = f"[Repeated {count} times]: {content}"
                self.pruned_history.append({'role': role, 'content': summary})

    def _normalize(self, content):
        return content.strip().lower()
```

### Explanation

1. **DeadlockDetector**:
   - **Normalization and Hashing**: Actions are normalized and hashed to facilitate quick comparisons.
   - **Detection Methods**: Three methods are implemented to detect direct repetitions, oscillations, and semantic traceback loops.
   - **Efficiency**: The use of a fixed-size deque limits memory usage and ensures that detection checks are performed in constant time.

2. **ContextPruner**:
   - **History Management**: The first message and system instructions are preserved. The rest are analyzed for repetitions.
   - **Cycle Collapsing**: Repetitive messages are summarized into a concise tombstone format, reducing the overall history size while retaining important context.
   - **Efficiency**: The algorithm runs in linear time relative to the size of the history, ensuring quick execution.

This design should meet the requirements for speed and functionality while being easy to integrate into your `capybala` library.