# Phase 2 Key Learnings

## Serpent Output Parsing

### The Problem

Factorio's `serpent.line()` outputs with **spaces around `=`** and **variable field order**:

```
Expected: {x=123.5,y=-45.2}
Actual:   {x = 123.5, y = -45.2}

Expected: {name="chest",count=1}
Actual:   {count = 1, name = "chest"}
```

### Solution

Use `\s*` in regex patterns to tolerate spaces:

```python
# WRONG - expects no spaces
pattern = r'x=([-\d.]+)'

# CORRECT - tolerates spaces
pattern = r'x\s*=\s*([-\d.]+)'
```

For complex structures, search each field separately:

```python
# Search fields independently (handles any order)
name = re.search(r'name\s*=\s*"([^"]+)"', block)
count = re.search(r'count\s*=\s*(\d+)', block)
```

### Debug Approach

Always print raw output first:
```python
raw = rcon.send_command('/c rcon.print(serpent.line(...))')
print(f"Raw: '{raw}'")
```

## Checklist for New Tools

- [ ] Checked raw output format?
- [ ] Regex patterns use `\s*` around `=`?
- [ ] Fields searched separately (not fixed order)?
- [ ] Tested with running Factorio?
