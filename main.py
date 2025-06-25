#!/usr/bin/env python3
import traceback

import tcod

import colour
import exceptions
import input_handlers
import setup_game


def main() -> None:
    # Defining variables for screen, map, rooms etc.
    # TODO: move to json to clean up and fix size
    screen_width = 80
    screen_height = 50

    # What font to use (the one saved in the repo)
    tileset = tcod.tileset.load_tilesheet(
        'dejavu10x10_gs_tc.png',
        32,
        8,
        tcod.tileset.CHARMAP_TCOD,
    )

    handler: input_handlers.BaseEventHandler = setup_game.MainMenu()

    # Create the screen
    # Definisng vsync is slightly redundant but all the best
    # games have it!!
    with tcod.context.new_terminal(
        screen_width,
        screen_height,
        tileset=tileset,
        title='Game',
        vsync=True,
    ) as context:
        # Creates the console we are drawing to
        # n.p order= 'F' reverses numpys unintuitive [y,x] notation
        root_console = tcod.console.Console(screen_width, screen_height, order='F')

        # Game loop
        try:
            while True:
                root_console.clear()
                handler.on_render(console=root_console)
                context.present(root_console)

                try:
                    for event in tcod.event.wait():
                        context.convert_event(event)
                        handler = handler.handle_events(event)
                except Exception:  # Handle exceptions in game
                    traceback.print_exc()  # Print error to stderr
                    # Then print the error to the message log
                    if isinstance(handler, input_handlers.EventHandler):
                        handler.engine.message_log.add_message(traceback.format_exc(), colour.error)
        except exceptions.QuitWithoutSaving:
            raise
        except SystemExit:  # Save and quit
            # //TODO: Add save function here
            raise
        except BaseException:  # Save on any other unexpected error
            # //TODO: Add the save function here
            raise


if __name__ == '__main__':
    main()
