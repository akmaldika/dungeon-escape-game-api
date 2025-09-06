from __future__ import annotations

from typing import Dict, Any, List, Optional, Tuple
from fastapi import HTTPException

from src.core import input_handlers  # consistent src import

from .state import ThreadSafeGameState, compute_legal_actions_unlocked


def build_observation_payload(game_state: ThreadSafeGameState) -> Dict[str, Any]:
    import base64
    with game_state.lock:
        engine = game_state.engine
        renderer = game_state.renderer
        handler = game_state.handler
        if (not engine or not renderer or 
            not isinstance(handler, (input_handlers.MainGameEventHandler, input_handlers.GameDoneEventHandler, input_handlers.GameOverEventHandler))):
            raise HTTPException(status_code=400, detail="No active game session")

        gm = engine.game_map
        # Ensure latest render into surface
        renderer.render_complete(engine)
        png = renderer.get_screenshot_bytes()
        b64 = base64.b64encode(png).decode('ascii')

        # Termination flags
        is_done = False
        end_reason: Optional[str] = None
        if getattr(engine, 'game_done', False):
            is_done, end_reason = True, 'victory'
        elif not engine.player.is_alive:
            is_done, end_reason = True, 'death'

        # Visible-only entities/items (respect FOV)
        enemies: List[Dict[str, Any]] = []
        for a in gm.actors:
            if a is engine.player:
                continue
            if gm.visible[a.x, a.y]:
                enemies.append({
                    'name': a.name, 'x': a.x, 'y': a.y,
                    'hp': a.fighter.hp, 'power': a.fighter.power,
                })
        items: List[Dict[str, Any]] = []
        for it in gm.items:
            if gm.visible[it.x, it.y]:
                items.append({'name': it.name, 'x': it.x, 'y': it.y})

        stairs: Optional[Tuple[int, int]] = None
        if hasattr(gm, 'downstairs_location'):
            sx, sy = gm.downstairs_location
            if gm.visible[sx, sy]:
                stairs = (sx, sy)

        # Row-major mask for ML usage
        visible_mask = gm.visible[:gm.width, :gm.height].T.tolist()
        legal_actions = compute_legal_actions_unlocked(engine)

        # Stacked messages for this step
        message_log: List[str] = []
        if hasattr(engine, '_current_step_messages'):
            for msg in engine._current_step_messages:
                c = msg.get('count', 1)
                t = msg.get('text', '')
                message_log.append(f"{t} (x{c})" if c > 1 else t)

        return {
            'step_id': game_state.current_level_step_count,
            'dungeon_level': engine.get_current_level(),
            'is_done': is_done,
            'end_reason': end_reason,
            'screenshot_png_base64': b64,
            'player': {
                'x': engine.player.x, 'y': engine.player.y,
                'hp': engine.player.fighter.hp, 'power': engine.player.fighter.power,
            },
            'enemies': enemies,
            'items': items,
            'stairs': stairs,
            'visible_mask': visible_mask,
            'legal_actions': legal_actions,
            'message_log': message_log,
        }


__all__ = ["build_observation_payload"]
