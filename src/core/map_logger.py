"""Map logging system untuk menyimpan generated maps ke file txt."""
from __future__ import annotations

import os
import json
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from src.core.game_map import GameMap
	from src.core import tile_types


class MapLogger:
	"""Logger untuk menyimpan map yang di-generate ke dalam file txt."""
	
	def __init__(self, base_path: str = "log"):
		self.base_path = base_path
		self.metadata_file = os.path.join(base_path, "data.json")
		
		# Buat direktori jika belum ada
		os.makedirs(os.path.join(base_path, "procedural"), exist_ok=True)
		os.makedirs(os.path.join(base_path, "string"), exist_ok=True)
		os.makedirs(os.path.join(base_path, "custom"), exist_ok=True)
		
		# Load atau inisialisasi metadata
		self.metadata = self._load_metadata()
	
	def _load_metadata(self) -> dict:
		"""Load metadata dari file JSON."""
		if os.path.exists(self.metadata_file):
			with open(self.metadata_file, 'r') as f:
				return json.load(f)
		return {"maps": []}
	
	def _save_metadata(self):
		"""Simpan metadata ke file JSON."""
		with open(self.metadata_file, 'w') as f:
			json.dump(self.metadata, f, indent=2)
	
	def log_map(self, game_map: GameMap, mode: str, floor: int):
		"""
		Simpan map ke file txt dan update metadata.
		
		Args:
			game_map: GameMap object yang akan disimpan
			mode: Mode game ('procedural', 'string', 'custom')
			floor: Floor level saat ini
		"""
		from src.core import tile_types
		
		timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
		filename = f"floor_{floor}_{timestamp}.txt"
		
		# Tentukan subfolder berdasarkan mode
		subfolder = mode
		filepath = os.path.join(self.base_path, subfolder, filename)
		
		# Konversi map ke string
		map_string = self._convert_map_to_string(game_map)
		
		# Simpan ke file
		with open(filepath, 'w') as f:
			f.write(map_string)
		
		# Update metadata
		map_info = {
			"floor": floor,
			"mode": mode,
			"width": game_map.width,
			"height": game_map.height,
			"timestamp": timestamp,
			"datetime": datetime.now().isoformat(),
			"file": f"{subfolder}/{filename}"
		}
		self.metadata["maps"].append(map_info)
		self._save_metadata()
		
		return filepath
	
	def _convert_map_to_string(self, game_map: GameMap) -> str:
		"""
		Konversi GameMap ke string representation.
		
		Mapping:
		# = wall (blocked)
		. = floor (walkable)
		  = void (space)
		@ = player
		> = stairs
		O = Ghost
		T = Red Ghost (Troll)
		h = Health Potion
		"""
		from src.core import tile_types
		
		lines = []
		for y in range(game_map.height):
			line = []
			for x in range(game_map.width):
				tile = game_map.tiles[x, y]
				
				# Cek entity di posisi ini
				entity_char = self._get_entity_char_at(game_map, x, y)
				if entity_char:
					line.append(entity_char)
				# Cek tile type
				elif tile == tile_types.wall:
					line.append('#')
				elif tile == tile_types.floor:
					line.append('.')
				elif tile == tile_types.down_stairs:
					line.append('>')
				elif tile == tile_types.void:
					line.append(' ')
				else:
					line.append(' ')
			
			lines.append(''.join(line))
		
		return '\n'.join(lines)
	
	def _get_entity_char_at(self, game_map: GameMap, x: int, y: int) -> str | None:
		"""Dapatkan karakter entity di posisi tertentu."""
		for entity in game_map.entities:
			if entity.x == x and entity.y == y:
				if entity.name == "Player":
					return '@'
				elif entity.name == "Ghost":
					return 'O'
				elif entity.name == "Red Ghost":
					return 'T'
				elif entity.name == "Health Potion":
					return 'h'
		return None


# Global instance
_map_logger = None


def get_map_logger() -> MapLogger:
	"""Get atau create global MapLogger instance."""
	global _map_logger
	if _map_logger is None:
		_map_logger = MapLogger()
	return _map_logger
