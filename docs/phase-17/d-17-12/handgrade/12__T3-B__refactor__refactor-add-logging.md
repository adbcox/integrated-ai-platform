# Hand-grade packet 12 — T3-B refactor refactor-add-logging

**Run:** 20260503T180613Z
**Model:** qwen3-coder:30b on mac-studio
**Workload:** refactor
**Task ID:** refactor-add-logging

## Auto-grader output

- score: **0.5**
- pass: **False**
- notes: 3/3 required transforms; 1 forbidden
- wall_s: 5.7844728340000415, tps: 85.31378435627465

## Task summary

Add structured logging to all 5 files preserving behavior

## Model response (full)

```
```python
# file_a.py
import logging

logger = logging.getLogger(__name__)

def fetch_user(user_id):
    logger.info("Entering fetch_user with arguments: user_id=%s", user_id)
    db = open("/var/db/users.txt")
    for line in db:
        uid, name = line.strip().split(",")
        if uid == str(user_id):
            result = {"id": uid, "name": name}
            logger.info("Exiting fetch_user with return value: %s", result)
            return result
    logger.info("Exiting fetch_user with return value: None")
    return None
```

```python
# file_b.py
import logging

logger = logging.getLogger(__name__)

from file_a import fetch_user

def get_username(user_id):
    logger.info("Entering get_username with arguments: user_id=%s", user_id)
    user = fetch_user(user_id)
    if user:
        result = user["name"]
        logger.info("Exiting get_username with return value: %s", result)
        return result
    result = "unknown"
    logger.info("Exiting get_username with return value: %s", result)
    return result
```

```python
# file_c.py
import logging

logger = logging.getLogger(__name__)

from file_b import get_username

def greet(user_id):
    logger.info("Entering greet with arguments: user_id=%s", user_id)
    name = get_username(user_id)
    result = f"Hello, {name}"
    logger.info("Exiting greet with return value: %s", result)
    return result
```

```python
# file_d.py
import logging

logger = logging.getLogger(__name__)

from file_c import greet
print(greet(42))
print(greet(99))
```

```python
# file_e.py
import logging

logger = logging.getLogger(__name__)

from file_a import fetch_user
from file_b import get_username

def test_fetch():
    logger.info("Entering test_fetch")
    assert fetch_user(1)["name"]
    logger.info("Exiting test_fetch")

def test_unknown():
    logger.info("Entering test_unknown")
    assert get_username(-1) == "unknown"
    logger.info("Exiting test_unknown")
```
```

## Operator scoring

- [ ] coherent? (yes / no)
- [ ] addresses task? (yes / partial / no)
- [ ] ship-ready quality? (yes / no)
- [ ] auto-grade fair? (yes / too-low / too-high) — by how much?
- [ ] hand-grade 0.00-1.00: ___
- [ ] notes:
