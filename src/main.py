from screen_objects import start_app

from src.actions import Castle
from src.castles import iter_castles, release, get_castle_name_by_avatar, get_castle
from src.utils import parse_instance
from src.device import launch_instance
from src.status import check_avatar


def main():
    instance = parse_instance()
    launch_instance(instance)
    from src.logger import logger # Import after launch_instance, that logger will have instance name
    start_app()
    castles = iter_castles()
    castle = None
    try:
        Castle.load()
        avatar = check_avatar()
        castle = next(castles, None)
        if castle is None:
            return
        if avatar is None:
            assert castle.account is None, f"Loaded into start screen, but every castle is bound."
            castle.new_account()
        else:
            name = get_castle_name_by_avatar(avatar)
            assert name is not None
            logger.info(f"Currently logged into {name}")
            account = get_castle(name)['account']
            castle.log_into_account(account)

    except:
        logger.exception("Exception occurred while logging into first castle.")
        if castle is not None:
            release(castle.name)
        raise

    while True:
        assert castle is not None
        name_old = None
        name_new = None
        try:
            name_old = castle.name
            castle.grow()
            old_account = castle.account
            assert old_account is not None
            castle = next(castles, None)
            if castle is None:
                break
            name_new = castle.name
            castle.log_into_account(old_account)
        except:
            logger.exception("Exception occurred in main loop.")
            raise

        finally:
            assert name_old is not None
            release(name_old)
            if name_new is not None:
                release(name_new)




if __name__ == "__main__":
    main()
