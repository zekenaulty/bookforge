# Run Scene Lint Help

## CLI
```bash
python skills/bookforge/run/scene-lint/skill.py --dump-example > params.json
python skills/bookforge/run/scene-lint/skill.py --dry-run --params-file params.json
python skills/bookforge/run/scene-lint/skill.py --params-file params.json
```

## Python
```python
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

path = Path("skills/bookforge/run/scene-lint/skill.py")
spec = spec_from_file_location("bookforge_skill", path)
module = module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

result = module.run(module.SKILL.example_params, dry_run=True)
print(result["user_prompt"])
```
