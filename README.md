# How to run

Note: playwright requires a chromium browser binary which is 1.4GB to download / on disk.

## With python
```
pip install requests playwright
playwright install chromium
python main.py ECHO360_URL
```

## With nix
Using nix run (no git clone required):
```
nix run github:dioxyq/echo360-normalise -- ECHO360_URL
```
Using nix develop
```
nix develop
python main.py ECHO360_URL
```
