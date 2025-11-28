# Map Logging Directory

Direktori ini menyimpan semua map yang di-generate oleh game.

## Struktur:

- `data.json` - Metadata semua map (floor, mode, dimensions, timestamp)
- `procedural/` - Map yang di-generate secara procedural
- `string/` - Map yang dibuat dari string via API
- `custom/` - Map yang di-load dari file

## Format Map File:

```
# = wall (blocked)
. = floor (walkable)
  = void (black space)
@ = Player
> = Stairs
O = Ghost
T = Red Ghost
h = Health Potion
```
