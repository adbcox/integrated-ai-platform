```python
# bin/test_analyze_task.py
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from analyze_task import main

@pytest.fixture
def setup_repo_root(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "analyze_task.py").touch()
    return repo_root

@patch('analyze_task.TaskRouter')
def test_main_happy_path(mock_router, setup_repo_root):
    mock_route = MagicMock()
    mock_router.return_value.classify.return_value = mock_route
    description = "Test task"
    files = ["file1.txt", "file2.txt"]
    
    with patch.object(sys, 'argv', ['analyze_task.py', description] + files[5D[K
files):
        main()
    
    mock_router.assert_called_once_with(setup_repo_root)
    mock_router.return_value.classify.assert_called_once_with(description, [K
files)

@patch('analyze_task.TaskRouter')
def test_main_no_files(mock_router, setup_repo_root):
    mock_route = MagicMock()
    mock_router.return_value.classify.return_value = mock_route
    description = "Test task"
    
    with patch.object(sys, 'argv', ['analyze_task.py', description]):
        main()
    
    mock_router.assert_called_once_with(setup_repo_root)
    mock_router.return_value.classify.assert_called_once_with(description, [K
None)

@patch('analyze_task.TaskRouter')
def test_main_invalid_args(mock_router):
    with pytest.raises(SystemExit) as excinfo:
        with patch.object(sys, 'argv', ['analyze_task.py']):
            main()
    
    assert excinfo.value.code == 1
```

```python
# bin/test_batch_coding_tasks.py
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from batch_coding_tasks import main

@pytest.fixture
def setup_repo_root(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "batch_coding_tasks.py").touch()
    return repo_root

@patch('batch_coding_tasks.TaskRouter')
def test_main_happy_path(mock_router, tmp_path):
    mock_route = MagicMock()
    mock_router.return_value.classify.return_value = mock_route
    task_file = str(tmp_path / "tasks.json")
    
    with patch.object(sys, 'argv', ['batch_coding_tasks.py', '--task-file',[14D[K
'--task-file', task_file]):
        main()
    
    Path(task_file).touch()  # Ensure the file exists
    mock_router.assert_called_once_with(Path.cwd())
    mock_router.return_value.classify.assert_not_called()

@patch('batch_coding_tasks.TaskRouter')
def test_main_task_file_does_not_exist(mock_router):
    with pytest.raises(SystemExit) as excinfo:
        task_file = str(tmp_path / "nonexistent.json")
        with patch.object(sys, 'argv', ['batch_coding_tasks.py', '--task-fi[10D[K
'--task-file', task_file]):
            main()
    
    assert excinfo.value.code == 1
```

```python
# bin/test_decompose_task.py
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from decompose_task import main

@pytest.fixture
def setup_repo_root(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "decompose_task.py").touch()
    return repo_root

@patch('decompose_task.TaskRouter')
def test_main_happy_path(mock_router, tmp_path):
    mock_route = MagicMock()
    mock_router.return_value.classify.return_value = mock_route
    description = "Test task"
    
    with patch.object(sys, 'argv', ['decompose_task.py', description]):
        main()
    
    mock_router.assert_called_once_with(REPO_ROOT)
    mock_router.return_value.classify.assert_called_once_with(description)

@patch('decompose_task.TaskRouter')
def test_main_invalid_args(mock_router):
    with pytest.raises(SystemExit) as excinfo:
        with patch.object(sys, 'argv', ['decompose_task.py']):
            main()
    
    assert excinfo.value.code == 1
```

```python
# bin/test_generate_tests.py
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from generate_tests import TestGenerator

@pytest.fixture
def setup_repo_root(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "generate_tests.py").touch()
    return repo_root

@patch('generate_tests.subprocess.run')
def test_generate_tests_happy_path(mock_subprocess, tmp_path):
    mock_subprocess.return_value.returncode = 0
    task_file = str(tmp_path / "tasks.json")
    
    with patch.object(sys, 'argv', ['generate_tests.py', '--task-file', tas[3D[K
task_file]):
        TestGenerator().generate()
    
    Path(task_file).touch()  # Ensure the file exists
    mock_subprocess.assert_called()

@patch('generate_tests.subprocess.run')
def test_generate_tests_invalid_task_file(mock_subprocess):
    with pytest.raises(SystemExit) as excinfo:
        task_file = str(tmp_path / "nonexistent.json")
        with patch.object(sys, 'argv', ['generate_tests.py', '--task-file',[14D[K
'--task-file', task_file]):
            TestGenerator().generate()
    
    assert excinfo.value.code == 1
```

```python
# bin/test_learning_insights.py
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from learning_insights import print_summary

@pytest.fixture
def setup_repo_root(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "learning_insights.py").touch()
    return repo_root

@patch('learning_insights.LearningDomain')
def test_print_summary_happy_path(mock_domain, tmp_path):
    mock_learning_domain = MagicMock()
    mock_domain.return_value = mock_learning_domain
    domain = LearningDomain()
    
    print_summary(domain)
    
    mock_domain.assert_called_once_with()
```

```python
# bin/test_local_coding_task.py
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from local_coding_task import main

@pytest.fixture
def setup_repo_root(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "local_coding_task.py").touch()
    return repo_root

@patch('local_coding_task.subprocess.run')
def test_main_happy_path(mock_subprocess, tmp_path):
    mock_subprocess.return_value.returncode = 0
    description = "Test task"
    
    with patch.object(sys, 'argv', ['local_coding_task.py', '--description'[15D[K
'--description', description]):
        main()
    
    mock_subprocess.assert_called()

@patch('local_coding_task.subprocess.run')
def test_main_invalid_args(mock_subprocess):
    with pytest.raises(SystemExit) as excinfo:
        with patch.object(sys, 'argv', ['local_coding_task.py']):
            main()
    
    assert excinfo.value.code == 1
```

```python
# bin/test_review_changes.py
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from review_changes import main

@pytest.fixture
def setup_repo_root(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "review_changes.py").touch()
    return repo_root

@patch('review_changes.subprocess.run')
def test_main_happy_path(mock_subprocess, tmp_path):
    mock_subprocess.return_value.returncode = 0
    description = "Test task"
    
    with patch.object(sys, 'argv', ['review_changes.py', '--description', d[1D[K
description]):
        main()
    
    mock_subprocess.assert_called()

@patch('review_changes.subprocess.run')
def test_main_invalid_args(mock_subprocess):
    with pytest.raises(SystemExit) as excinfo:
        with patch.object(sys, 'argv', ['review_changes.py']):
            main()
    
    assert excinfo.value.code == 1
```

```python
# bin/test_route_task.py
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from route_task import main

@pytest.fixture
def setup_repo_root(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "route_task.py").touch()
    return repo_root

@patch('route_task.TaskRouter')
def test_main_happy_path(mock_router, tmp_path):
    mock_route = MagicMock()
    mock_router.return_value.classify.return_value = mock_route
    description = "Test task"
    
    with patch.object(sys, 'argv', ['route_task.py', description]):
        main()
    
    mock_router.assert_called_once_with(Path.cwd())
    mock_router.return_value.classify.assert_called_once_with(description)

@patch('route_task.TaskRouter')
def test_main_invalid_args(mock_router):
    with pytest.raises(SystemExit) as excinfo:
        with patch.object(sys, 'argv', ['route_task.py']):
            main()
    
    assert excinfo.value.code == 1
```