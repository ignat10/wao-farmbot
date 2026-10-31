from datetime import datetime, timedelta, timezone
from functools import cached_property
from itertools import chain
from random import randrange, choice, sample
from time import sleep, perf_counter

from screen_objects import (
    back,
    tap_center,
    swipe_center,
    start_app,
    close_app,
    reset_screen,
    write,
    SwipeSpeed,
    Direction,
    ScreenObject,
)

from src.device import shake
from src.castles import get_column, update_castle
from src.objects import (
    objects,
    avatars,
    bug_levels,
    troops,
    equipment,
    resources_technology,
    castle_levels,
    march_limits,
)
from src.paths import CASTLES_DB_PATH
from src.status import (
    CastleStatus,
    MineType,
    Task,
    check_castle_status,
)
from src.logger import logger
from src.utils import log_raise

MAX_MINE_LEVEL = 6
MINE_LEVELS_SEQUENCE = [5, 6, 4, 3, 2, 1]

SWIPE_DIRECTIONS = (Direction.Up, Direction.Down, Direction.Right, Direction.Left)


def restart_app():
    close_app()
    sleep(4.5)
    start_app()


def value_assert(name: str, value: object, typ: type) -> None:
    val = value
    assert isinstance(
        val, typ
    ), f"{name} in {CASTLES_DB_PATH} should be {typ.__name__}, got '{val.__repr__() if not isinstance(val, (timedelta, DataTableFormula, ArrayFormula)) else "value doesn't impl repr method"}'"  # type: ignore


class Castle:
    def __init__(
        self,
        name: str,
        google: int,
        account: int | None,
        avatar: int | None,
        last_login: str,
    ):

        value_assert("name", name, str)
        value_assert("google", google, int)
        if account is not None:
            value_assert("account", account, int)
        if avatar is not None:
            value_assert("avatar", avatar, int)
            assert 0 <= avatar <= 14, f"avatar in {CASTLES_DB_PATH} must be between 0 and 14"
        self.name = name
        self._google = google
        self._account = account
        self._avatar = avatar
        self._last_login = last_login

        self.no_speed: int = 0
        self.last_gather_at: datetime | None = None
        self.stamina = True
        self.mine_type = (
            (level, mine)
            for level in MINE_LEVELS_SEQUENCE
            for mine in MineType
            if mine == MineType.FOOD
            or mine == MineType.WOOD
            or (mine == MineType.STONE and self.level >= 10)
            or (mine == MineType.IRON and self.level >= 15)
        )
        self.is_enough_troops = True
        self.elite_mines_got: set[int] = set()


    @property
    def google(self) -> int:
        return self._google

    @google.setter
    def google(self, value: int):
        update_castle(self.name, "google", value)
        self._google = value

    @property
    def account(self) -> int | None:
        return self._account

    @account.setter
    def account(self, value: int):
        update_castle(self.name, "account", value)
        self._account = value

    @property
    def avatar(self) -> int | None:
        return self._avatar

    @avatar.setter
    def avatar(self, value: int | None):
        update_castle(self.name, "avatar", value)
        self._avatar = value

    @property
    def last_login_minutes(self) -> int:
        last_login = datetime.fromisoformat(self._last_login).replace(tzinfo=timezone.utc)
        minutes = int((datetime.now(timezone.utc) - last_login).total_seconds()) // 60
        return minutes

    @property
    def last_gather_ago(self) -> int | None:
        """Return elapsed gather time in seconds."""
        if self.last_gather_at is None:
            return None
        return int((datetime.now() - self.last_gather_at).total_seconds())

    def set_last_gather_now(self) -> None:
        """Mark gathering as having happened just now."""
        self.last_gather_at = datetime.now()

    @cached_property
    def marches(self) -> int:
        """gets available marches value. From 1 to 4"""
        objects["lord_info"].force_tap(5)
        if not objects["check_details"].tap(5):
            self.close_ad()
            return self.marches
        sleep(2)
        for limit, obj in march_limits.items():
            if obj.exists():
                logger.info(f"saved {self.name} 1 + {limit} marches")
                self.close_ad()
                assert (
                    0 <= limit <= 3
                ), f"additional marches value must be in range 0..3, got {limit}"
                return limit + 1
        log_raise("No march num found in march_limit.")

    @staticmethod
    def close_bella() -> bool:
        if not objects["bella"].exists():
            return False
        while objects["bella"].tap():
            sleep(1.5)
        return True

    def new_account(self) -> None:
        """creates new account, upgrades castle to level 4. from city or map."""
        if self.account is not None:
            return
        if objects["avatar"].tap():
            objects["account"].force_tap()
            objects["new_game"].force_tap()
            objects["confirm"].force_tap()
            objects["realm"].force_tap()
            logger.info("account created")

        objects["man"].force_exists(100)
        swipe_center(Direction.Up, SwipeSpeed.Slow, 1.7)
        swipe_center(Direction.Right, SwipeSpeed.Slow, 0.75)
        sleep(15)
        swipe_center(Direction.Up, SwipeSpeed.Fast, 0.9)
        swipe_center(Direction.Right, SwipeSpeed.Fast, 0.8)
        self.kill_monsters()
        logger.info("finished 0 level")
        objects["bella"].force_exists(30)
        self.close_bella()
        self.challenge()  # first level
        logger.info("finished 1st level")
        sleep(1.5)
        self.close_bella()
        self.challenge()
        logger.info("finished 2nd level")
        objects["bella"].force_exists()
        self.close_bella()
        restart_app()
        objects["bella"].force_exists(300)
        self.close_bella()
        objects["first_castle"].force_tap()
        sleep(1)
        objects["upgrade"].force_tap()
        objects["upgrade_blue"].force_tap()
        objects["bella"].force_exists()
        self.close_bella()
        objects["new_monster"].force_tap()
        self.challenge()
        logger.info("finished 3rd level")
        objects["backhand"].force_tap()
        objects["bella"].force_exists()
        self.close_bella()
        objects["kingroad"].force_tap()
        sleep(1.5)
        back()
        sleep(1)
        self.bind_account()
        self.claim_mail()
        self.change_name()
        self.change_avatar()
        logger.info(f"account created, named and bound")

    @classmethod
    def challenge(cls) -> None:
        logger.info("challenging")
        while not (objects["man"].exists() or objects['blue_bonus'].exists()):
            for obj in bug_levels:
                obj.tap()
            objects["challenge"].tap() or objects["bright_challenge"].tap()
            reset_screen()
            sleep(1)
        cls.kill_monsters()

    @classmethod
    def kill_monsters(cls) -> None:
        logger.info("killing monsters")
        for _ in range(50):
            if (
                objects["quest_complete"].tap()
                or objects["quit"].tap()
                or objects["backhand"].exists()
            ):
                break
            elif objects["blue_bonus"].tap():
                objects["confirm_bonus"].exists(3)
            if objects["confirm_bonus"].tap():
                sleep(1.2)
            else:
                swipe_center(choice(SWIPE_DIRECTIONS), SwipeSpeed.Slow, 4)
            sleep(1)
        sleep(1.5)

    def change_name(self) -> None:
        objects["avatar"].force_tap(3)
        if objects["x_news"].tap(1.3):
            sleep(1.5)
        objects["change_name"].force_tap(4)
        sleep(0.9)
        objects["2-16_characters"].force_tap(5)
        sleep(1.2)
        write(self.name)
        sleep(3)
        objects["change_name_green"].force_tap(5)
        sleep(1.5)
        if objects["change_name_green"].exists():
            log_raise(f"Name {self.name} already taken.")
        self.close_ad()
        logger.info("name has been changed")

    def change_avatar(self) -> None:
        objects["avatar"].force_tap(3)
        if objects["x_news"].tap(1):
            sleep(1)
        objects["switch_arrows"].force_tap(10)
        sleep(1)
        objects['pick_avatar'].force_exists(10)
        assert objects['pick_avatar'].count() == 15
        avatar = randrange(4, 15)
        objects['pick_avatar'].force_tap(index=avatar)
        objects['switch_avatar'].force_tap(10)
        objects['confirm_use_stamina'].force_tap(10)
        self.avatar = avatar
        logger.info(f"successfully switched {self.name}'s avatar to {avatar}")
        self.close_ad()

    @cached_property
    def level(self) -> int:
        objects["avatar"].force_tap()
        if not objects["account"].exists(5):
            self.close_ad()
            return self.level
        reset_screen()
        sleep(1)
        for level, obj in castle_levels.items():
            if obj.exists():
                logger.info(f"saved {self.name} level {level}")
                self.close_ad()
                return level
        log_raise("No castle level found.")

    def bind_account(self):
        if self.account is not None:
            return
        gmail = self.google
        objects["avatar"].force_tap()
        objects["account"].force_tap(3)
        if not objects["undo_bind"].exists():
            objects["bind"].force_tap(3)
            if objects["gmail"].exists(40):
                objects["gmail"].force_tap(index=gmail)
        if objects["undo_bind"].exists(50):
            account_number = get_column("google").count(gmail) - 1  # self account
            logger.info(
                f"bound account {self.name} to {gmail} gmail. saved it as account number {account_number}"
            )
            self.account = account_number
        self.close_ad()

    def kingroad_task(self) -> bool:
        self.kingroad_claim()
        if not (
            objects["kingroad"].tap()
            or objects["hand"].tap()
            or objects["kingroad_go"].exists()
        ):
            self.close_ad()
            if not (objects["kingroad"].tap() or objects["hand"].tap()):
                logger.info("No kingroad!")
                return False
        if not objects["kingroad_go"].exists(3):
            self.close_ad()
            return self.kingroad_task()
        task = Task.check()
        logger.info(f"doing {task.name if task is not None else "unknown"} task")
        match task:
            case Task.UPGRADE:
                objects["kingroad_go"].force_tap(10)
                sleep(1)
                self.close_bella()
                if objects["hand"].tap(3):
                    if objects['kingroad_go'].exists(1):
                        self.kingroad_task()
                else:
                    tap_center()
                sleep(1)
                if objects["upgrade"].tap(2) or objects["hand"].tap():
                    sleep(2)
                    self._build_need()
                self.close_ad()
                return True
            case Task.POWER:
                if randrange(7) == 4:
                    self.to_map()
                    self.close_ad()
                self.heal()
                self.recruit(horses=False)
                return True
            case Task.RECRUIT:
                if randrange(5) == 4:
                    self.claim_recruits()
                    objects['kingroad'].force_tap(20)
            case Task.GATHER:
                objects['kingroad_go'].force_tap(20)
                sleep(2)
                self.close_bella()
                objects['book'].force_exists(20)
                sleep(2)
                if objects['hand'].tap(2):
                    objects['map_hand'].force_tap(5)
                    objects['map_hand'].force_tap(3)
                    objects["check"].force_exists(10)
                    if self.last_gather_ago > 1000:
                        self.withdraw()
                    else:
                        objects["gather"].tap(15)
                        sleep(1.5)
                        objects["gather"].tap(4)
                        objects["set_out"].tap(5)
                else:
                    self.get_std_mine()
                self.close_ad()
                return True

            case Task.SCOUT | Task.CONQUER | Task.RUINS:
                logger.info(f"castle {self.name}. {task.name} task have to be done manually.")
                self.close_ad()
                return False

        objects["kingroad_go"].force_tap(8)
        sleep(1.5)
        self.close_bella()
        if objects["loading"].exists():
            objects["book"].force_exists(30)
            sleep(2)

        while objects["hand"].tap(1):
            if objects["heroic_evoluation_blue"].tap(0.7):
                objects["evolve"].tap(5)
            if objects["go_blue"].tap():
                log_raise("UNKNOWN BEHAVIOUR, NEED TO BE CHECKED")
                # sleep(1)
                # return False
            objects["free"].tap() or objects['free_upgrade'].tap()
            if objects["kingroad_go"].tap():
                logger.info("tapped kingroad go inside hand loop")
            sleep(1)
            reset_screen()

        while objects["map_hand"].tap(1):
            if objects["arrow"].exists(1):
                break
        logger.info("no more hands")
        reset_screen()

        if objects['go'].exists():
            self.kill_monster()

        elif objects["alliance_bonuses"].tap():
            self.close_ad()
            self.join_alliance()
            return True

        if objects["unlock"].tap():
            logger.info("beast unlocked")
            sleep(20)

        elif objects["unlock_land"].tap():
            logger.info("unlocked land")
            sleep(0.8)

        elif objects["forge"].exists():
            self.forge()

        elif objects["go_research"].tap():
            if objects["horseshoes"].tap(2):
                sleep(0.8)
                objects["research_blue"].tap(2)

        elif objects["research"].exists():
            if not self.speed_up():
                self.research()

        elif objects["recruit"].tap():
            logger.info("recruiting")
            objects["recruit_blue"].exists(2)
        objects["recruit_blue"].tap()

        if objects["upgrade"].tap() or objects["upgrade_barracks"].tap():
            sleep(2)
        self._build_need()

        if objects["fortify"].tap():
            objects["one-tap_upgrade"].force_tap(2)
            if not objects["use_all"].tap(2):
                self.close_ad()
                self.conjure()
                return True

        if objects["sell"].tap():
            logger.info("shop")
            sleep(1.5)
            objects["shell"].tap_each()
            objects["buy"].force_tap(2)
            objects["shell"].exists()
            objects["shell"].tap_each()
            objects["confirm_shell"].tap(1)
            back()

        if not objects["green"].tap() and objects["switch_level"].tap():
            for _ in range(4):
                objects["green"].force_tap(index=randrange(15))

        if objects['no_suppress'].exists():
            back()
            sleep(1)
            objects['rebels'].force_exists(10)

        if rebels := objects["rebels"].count():
            objects['rebels'].force_tap(index=rebels - 1)
            sleep(1.5)
            self.close_bella()
            objects["suppress"].force_exists(10)

        if objects["suppress"].tap() and not objects["set_out"].tap(2):
            self.close_ad()
            self.to_map()
            self.withdraw()
            self.close_ad()
            return True
        else:
            objects['set_out'].tap()

        if objects["alliance_donate"].tap():
            sleep(1.5)
            objects["donate_blue"].tap(times=4, interval=0.6)
            objects["donate_confirm"].tap(3)

        elif objects["bright_challenge"].exists():
            self.challenge()
        if (
            objects["man"].exists()
            or objects["blue_bonus"].tap()
            or objects["confirm_bonus"].tap()
        ):
            self.kill_monsters()

        self.speed_up()
        self.close_ad()
        return True

    @classmethod
    def kingroad_claim(cls):
        """claims completed kingroad tasks"""
        objects["kingroad"].tap()
        if objects["kingroad_done"].tap(2):
            logger.info("finished kingroad chapter!")
            cls.close_ad()
            cls.kingroad_claim()
        else:
            reset_screen()
            while objects["kingroad_claim"].tap(0.7):
                logger.info("claimed kingroad task!")
                sleep(1.5)
                back()

    def log_into_account(self, green_regular_position: int) -> None:
        """logs into current account. from city or map."""
        if self.account is None:
            self.new_account()
            return
        assert (
            self.google is not None
        ), f"called log_into_account for {self.name}, but google was not set in {CASTLES_DB_PATH}"
        assert self.avatar is not None, f"called log_into_account for {self.name}, but avatar was not set in {CASTLES_DB_PATH}"

        while not avatars[self.avatar].exists(): #type: ignore
            logger.info(f"logging into {self.name}")
            reset_screen()
            self.close_ad()
            if objects["avatar"].tap():
                objects["account"].exists(4)
            if objects["account"].tap():
                objects["switch"].force_exists(15)
            if objects["switch"].tap():
                sleep(1.5)
            if not (objects["login"].tap(3) and objects["gmail"].exists(10)):
                continue
            objects["gmail"].force_tap(index=self.google)
            for _ in range(15):
                if objects["acc_list"].exists(1):
                    break
                elif objects['google_down'].tap(1):
                    objects['continue'].force_tap(10)
                    objects['acc_list'].exists(10)
            else:
                continue
            is_green = objects["green_castle"].exists() and self.account > green_regular_position
            if not objects["castle"].tap(index=self.account - is_green): # FIX: green castle might be in self.account number.
                log_raise("Google account cooldown.")
            objects["confirm"].force_tap(20)
            logger.info("logged in.")
            sleep(7.5)
            self.load()

    @classmethod
    def load(cls) -> None:
        start = perf_counter()
        reset_screen()
        logger.info("loading game")
        while check_castle_status() == CastleStatus.NOT_IN_CASTLE:
            reset_screen()
            if objects["man"].exists():
                return
            if objects['age'].tap():
                sleep(1)
                if objects['confirm_age'].tap(3):
                    logger.info("confirmed age")
            objects['x_ldplayer'].tap()
            if perf_counter() - start > 200:
                logger.info("loading timeout. restart app.")
                restart_app()
                cls.load()
                return
            sleep(1.5)
        logger.info("loaded.")
        cls.close_ad()

    @classmethod
    def close_ad(cls) -> None:
        """closes ad. from city or map"""
        for _ in range(4):
            if check_castle_status() == CastleStatus.CLOSED_AD:
                return
            if cls.close_bella():
                logger.info("closed bella. looking for hand.")
                sleep(1)
                while objects["hand"].tap(1):
                    objects["unlock"].tap(0.6)
                logger.info("end hand.")
            if objects["exit_game"].exists():
                logger.info("invalid token.")
                break
            if objects["help"].tap():
                sleep(0.5)
            else:
                objects["continue_game"].tap()
                objects["x"].tap()
                objects["x_new"].tap()
                objects["x_news"].tap()
                objects["x_swap"].tap()
                objects["claim_daily"].tap()
                objects["claim_temple"].tap()
                objects["check_beast"].tap()
            if check_castle_status() == CastleStatus.CLOSED_AD:
                return
            for _ in range(3):
                back()
                sleep(0.2)
            sleep(1)
            if check_castle_status() == CastleStatus.CLOSED_AD:
                return
            elif objects["no"].tap(3):
                sleep(1.5)
            else:
                tap_center()
        logger.info("unable to close. restart app.")
        restart_app()
        cls.load()

    @staticmethod
    def claim_rss():
        logger.info("shaking")
        shake()
        sleep(5)

    @classmethod
    def claim_quest(cls):
        if objects["quest"].tap():
            sleep(1.5)
            while objects["daily_quest_claim"].tap(0.4):
                back()
            while objects["claim_daily_quest"].tap(0.4):
                back()
            sleep(2.2)
            objects["growth_quest"].tap()
            for _ in range(3):
                while objects["claim_growth_quest"].tap(3):
                    if not objects["reward"].tap(10):
                        back()
                        sleep(1.5)
                        back()
                if not objects["another_growth_quest"].tap(2):
                    break
            cls.close_ad()

    @classmethod
    def claim_mail(cls) -> None:
        objects["mail"].force_tap()
        if objects["delete_mail"].tap(3):
            objects['confirm_use_stamina'].force_tap(10)
            sleep(2)
        for _ in range(objects["mail_reward"].count()):
            cls.close_ad()
            objects['mail'].force_tap()
            objects['mail_reward'].force_tap(10)
            if not objects["claim_torch"].tap(2):
                objects["read_claim_all"].force_tap(10)
                objects["confirm_green"].force_tap(10)
        cls.close_ad()

    @classmethod
    def claim(cls) -> None:
        """claims recruited troop and gift. from city"""
        cls.close_ad()
        objects["help"].tap()
        if objects["claim"].tap():
            sleep(1.5)
            back()
            sleep(1.5)

    @classmethod
    def events(cls) -> None:
        def event():
            if not objects["event"].exists():
                objects["events"].force_tap(10)
                objects["event"].force_exists(10)

        def claim_7_march(event_index: int = 0):
            event()
            if not objects["7-day_march"].tap():
                return

            sleep(0.5)
            objects["!"].exists(3)
            if objects["event_claim"].exists():
                objects["event_claim"].tap_each()
                sleep(0.5)
                back()
                back()
                cls.close_ad()
                claim_7_march(event_index + 1)
            elif objects["!"].tap(index=event_index):
                objects["event_claim"].exists(2)
                claim_7_march(event_index + 1)
            cls.close_ad()

        def claim_rise():
            event()
            if objects["rising_road"].tap() or objects['dragons_domain'].tap():
                sleep(2)
                while objects["event_arrow"].tap(4):
                    sleep(2)
                    back()
                cls.close_ad()

        def camel():
            event()
            if objects["camel"].tap():
                sleep(1)
                if objects["!"].tap(2):
                    sleep(2)
                    while objects['event_claim'].tap(2):
                        sleep(2)
                        back()
                    sleep(2)
                    if objects["!"].tap(index=1):
                        objects['event_claim'].force_exists(10)
                        while objects['event_claim'].tap(index=1):
                            sleep(1)
                            back()
                            sleep(2)
                cls.close_ad()

        def autumn_login():
            event()
            if objects['autumn_login'].tap():
                sleep(2)
                objects['event_claim'].tap_each()
                cls.close_ad()

        logger.info("claiming events rewards")
        claim_7_march()
        claim_rise()
        camel()
        autumn_login()
        cls.close_ad()

    def tasks(self) -> bool:
        if not objects['tasks'].tap(3):
            self.close_ad()
            if self.level < 5:
                return objects['tasks'].tap()
            else:
                objects['tasks'].force_tap(10)
        return True

    def pinata(self) -> None:
        if not self.tasks():
            return
        logger.info("claiming pinata")
        sleep(2)
        for _ in range(3):
            swipe_center(Direction.Up, SwipeSpeed.Turbo, 0.5)
            sleep(1)
        if objects['pinata_task'].tap(2) and objects['pinata'].exists(3):
            for _ in range(3):
                objects['pinata'].tap_each()
                if objects['try_luck'].tap(7):
                    sleep(2)
                    objects['card'].force_tap(10)
                    objects['free_crystal'].force_tap(10)
                    objects['fold'].force_tap(10)
                    objects['confirm_use_stamina'].force_tap(10)
                    objects['pinata'].exists(3)
        else:
            back()
            sleep(1)
        self.close_ad()

    @classmethod
    def upgrade_lord_skills(cls) -> None:
        logger.info("upgrading lord skills")
        objects["lord_info"].tap()
        if not objects["lord_skills"].tap(10):
            cls.close_ad()
            cls.upgrade_lord_skills()
            return
        objects["development_skills"].force_tap(10)
        sleep(0.5)
        while not objects["skill_points_0"].exists():
            if objects["upgrade_to_max"].exists():
                break
            while not objects["lord_skill"].tap(1):
                swipe_center(Direction.Up, SwipeSpeed.Fast, 0.4)
                sleep(1.5)
            objects["upgrade_to_max"].force_tap(3)
        cls.close_ad()

    @staticmethod
    def use_lord_skills() -> None:
        """use lord skills, harvest, gather speed up, recall all. from city or map"""
        logger.info("lord skills...")
        objects["lord"].tap()
        if objects["gather_speed_up"].tap(2):
            objects["use"].tap(2)
        if objects["harvest"].tap(2):
            objects["use"].tap(2)
        objects["recall_all"].tap(3)
        sleep(0.15)
        if not objects["use"].tap(2):
            back()
            objects["use"].tap(2)
        logger.info("lord skills done.")
        reset_screen()
        sleep(1.2)

    def confirm_rss(self) -> bool:
        if (mine := MineType.check_need()) is not None:
            self.mine_type = chain(
                ((level, mine) for level in MINE_LEVELS_SEQUENCE),
                self.mine_type,
            )
        return objects['confirm_rss'].tap()

    def heal(self) -> None:
        """heal troops in hospital and sanctuary, then claim healed. from castle."""
        if objects["claim_healed"].tap():
            logger.info("claimed healed")
            sleep(1.5)
        if objects["hospital"].tap():
            logger.info("healing...")
            objects["heal"].tap(3)
            sleep(1)
            if self.confirm_rss():
                sleep(1.5)
        if objects["ask_help"].tap(0.2):
            objects["sanctuary"].exists(2)
        if objects["sanctuary"].tap():
            logger.info("sanctuary...")
            objects["revive"].tap(3)
            objects["claim_holy_water"].tap(1)
            if not objects["confirm_green"].tap(1):
                objects["holy_quest"].tap(1)
                objects["claim_holy_quest"].tap(1)
                if objects["confirm_green"].tap(1):
                    sleep(0.8)
                objects["holy_revival"].tap(1)
            objects["revive"].tap(1)
            sleep(0.5)
            back()
            objects["hospital_building"].exists(2)
        if objects["hospital_building"].tap():
            sleep(1.5)
        if self.speed_up():
            sleep(2)
        objects["claim_healed"].tap()

    def speed_up(self) -> bool:
        if objects["no_speed"].exists() or objects['use_speed'].exists():
            self.no_speed += 1
            self.close_ad()
            return False

        if (
            objects["speed_up"].tap()
            or objects["speed_up_blue"].tap()
            or objects["get_now"].tap()
        ):
            sleep(1)
            self.no_speed += 1

        if objects["one-tap_speed_up"].tap() and objects["confirm_speed_up"].tap(3):
            sleep(1.5)
            self.no_speed -= 1
            return True

        return False

    def research(self) -> None:
        marches = self.marches
        level = self.level
        if not self.tasks():
            return
        objects["research_task"].force_tap(10)
        if not objects["military"].exists(2):
            objects["back"].force_tap()
            objects["military"].force_exists(10)
        if (
            marches == 1 and level >= 5
            or marches == 2 and level >=12
            or marches == 3 and level >=19
        ):
            logger.info(f"unlocking march number {marches + 1}")
            objects["military"].force_tap()
            match marches:
                case 2:
                    swipe_center(Direction.Up, SwipeSpeed.Normal, 1)
                case 3:
                    swipe_center(Direction.Up, SwipeSpeed.Turbo, 0.7)
            sleep(1)

            if not objects["legion"].tap(2):
                if not objects["leadership"].tap():
                    if not objects["horseshoes"].tap():
                        if not objects["expansion"].tap():
                            objects["draft"].force_tap()

        else:
            logger.info("researching resources technology.")
            objects["resources"].force_tap()
            sleep(3)
            for techno in sample(resources_technology, k=len(resources_technology)):
                if techno.tap():
                    if objects["research_blue"].exists(1.5):
                        break
                    else:
                        back()
                        sleep(1)

        if not objects["research_blue"].tap(1):
            if objects['go_research'].tap():
                sleep(1)
                objects['hand'].force_tap(2)
                sleep(1)
                objects['hand'].force_tap(2)
                sleep(2)
                self._build_need()
            elif objects['get_now_research'].exists():
                self.close_ad()
                if not objects['college_icon'].tap(2):
                    self.to_map()
                    self.close_ad()
                    objects['college_icon'].force_tap(10)
                sleep(2)
                self.speed_up()
        sleep(1)
        self.confirm_rss()
        self.close_ad()

    @classmethod
    def forge(cls) -> None:
        logger.info("forging")
        if objects["forge"].tap():
            sleep(0.8)
        max_item: ScreenObject | None = None
        max_num = 0
        for item in equipment:
            item.force_tap()
            sleep(0.8)
            n = objects["forge_green"].count()
            if n >= max_num:
                max_num = n
                max_item = item
            back()
            sleep(0.8)
        if max_item is not None:
            max_item.tap()
            objects["forge_green"].exists(10)
            objects["forge_green"].tap(index=max_num - 1)
            if objects["+"].tap(1):
                objects["select"].tap(3)
            objects["forge_blue"].tap(5)
        cls.close_ad()

    def _build_need(self) -> bool:
        """builds required for upgrade buildings. from upgrade menu."""
        for _ in range(10):
            reset_screen()

            if objects["free"].exists() or objects['free_upgrade'].exists():
                while objects['free'].tap(1) or objects['free_upgrade'].tap(1):
                    sleep(1)
                logger.info("built for free.")
                return True

            if self.confirm_rss():
                return True

            if MineType.check_need() is not None:
                logger.info("Not enough rss even with pack.")
                self.no_speed += 3
                return False

            if objects['purchase'].exists():
                logger.info("Not enough gems for hammer.")
                self.no_speed += 3
                return False

            if (
                objects["hand"].tap(1)
                or objects["upgrade_blue"].tap()
                or objects["big_upgrade_blue"].tap()
                or objects["hammer_use"].tap()
                or objects["hammer_200"].tap()
                or objects["go_upgrade"].tap()
            ):
                continue

        return self.speed_up()

    def upgrade_castle(self) -> None:
        """upgrades castle or required buildings."""
        if not objects["castle_building"].tap():
            self.to_map()
            self.close_ad()
            self.upgrade_castle()
        if objects["upgrade"].tap(2):
            sleep(2)
        self._build_need()
        self.close_ad()

    def build(self) -> bool:
        if not self.tasks():
            return False
        logger.info("building")
        if not objects["build_task"].tap(10):
            self.close_ad()
            return self.build()
        sleep(1)
        objects["hand"].tap(2)

        if objects["upgrade"].tap(1.5) or objects['hand'].tap():
            sleep(1.5)
        elif objects['kingroad_go'].exists() or objects['kingroad_claim'].exists():
            self.close_ad()
            return self.build()
        result = self._build_need()
        self.close_ad()
        return result

    def claim_recruits(self) -> None:
        if not self.tasks():
            return
        objects['recruit_task'].force_exists(10)
        barracks = objects['recruit_task'].count()
        back()
        sleep(2)
        for i in range(barracks):
            objects['tasks'].force_tap(10)
            if not objects['recruit_task'].exists(3):
                self.claim_recruits()
            objects['recruit_task'].force_tap(index=i)
            sleep(2)
            if not objects['hand'].tap(1):
                tap_center()
            if objects['speed_up'].exists(2):
                sleep(1)
                reset_screen()
                self.speed_up()
            self.close_ad()

    def recruit(self, *, horses: bool) -> None:
        """recruits horses."""
        if not self.tasks():
            return
        logger.info(f"recruiting {"horses" if horses else "powerful troops"}.")
        objects["recruit_task"].exists(1.5)
        barracks = objects["recruit_task"].count()
        back()
        sleep(2)
        for i in range(barracks * 2):
            self.close_ad()
            objects["tasks"].force_tap(5)
            sleep(1.5)
            objects["recruit_task"].tap(index=i % barracks)
            sleep(1)
            objects["hand"].tap(4)
            sleep(1)
            if not objects["recruit"].tap(1):
                objects["free"].tap()
                continue
            if not objects["recruit_blue"].exists(2):
                self.speed_up()
                if not objects['recruit_blue'].exists(1):
                    continue
            if objects["x_news"].tap():
                sleep(1.5)
            if horses:
                objects["cavalry"].tap(1)
                sleep(1.2)
                objects["previous"].tap(times=8, interval=0.02)
                sleep(0.3)
                objects["second"].force_tap(10)
                if objects['upgrade_barracks'].tap(2):
                    sleep(1)
                    self._build_need()
                    self.close_ad()
                    continue
            else:
                choice(troops).tap(1)
                sleep(0.2)
            objects['recruit_blue'].force_tap(5)
            sleep(1)
            self.confirm_rss()
        back()
        sleep(0.5)

    @classmethod
    def conjure(cls):
        if not objects['altar'].tap():
            cls.to_map()
            cls.close_ad()
            objects['altar'].force_tap(10)
        sleep(2)
        objects['conjure'].force_tap(10)
        objects['conjure_10_times'].force_exists(10)
        for i in [1, 0]:
            objects['conjure_10_times'].force_tap(index=i)
            if objects['confirm_use_stamina'].tap(2):
                break
            back()
            reset_screen()
            sleep(1)
        cls.close_ad()

    @classmethod
    def use_pack(cls):
        """Uses items from the pack."""
        cls.close_ad()
        objects["pack"].force_tap()
        sleep(1.5)
        for i in range(objects["use_blue"].count()):
            if not objects["use_blue"].exists(1):
                cls.close_ad()
                objects["pack"].force_tap()
                objects["use_blue"].force_exists(5)
            if not objects["use_blue"].tap(index=i):
                break
            if objects["use_all_items"].tap(1):
                objects["use_all"].force_tap(10)
                continue
            else:
                objects["max_items"].tap()
            objects["use_item"].tap(1)
        cls.close_ad()

    @classmethod
    def join_alliance(cls) -> None:
        logger.info(f"joining alliance.")
        objects['alliance'].force_tap()
        if objects['alliance_bonuses'].exists(2):
            back()
            objects['apply'].exists(2)
        if not (objects['apply'].exists() or objects['join'].exists() or objects['applying'].exists()):
            cls.close_ad()
            return
        for _ in range(10):
            if objects['join'].tap():
                break
            objects["apply"].tap_each()
            swipe_center(Direction.Up, SwipeSpeed.Fast, 0.5)
            sleep(2)
        cls.close_ad()

    # TODO: add the remaining reward-claim flows:
    #
    # Alliance:
    #   - gifts
    #
    # Events:
    #   - add the remaining events
    #
    # City buildings:
    #   - safe resources
    #   - Castle Growth Map

    @classmethod
    def alliance_rewards(cls) -> None:
        objects['alliance'].force_tap()
        if objects['alliance_quest'].tap(3):
            objects['claim_all'].tap(2)
            cls.close_ad()
            objects['alliance'].force_tap()
            sleep(1.5)
        swipe_center(Direction.Up, SwipeSpeed.Slow, 1)
        objects['fiend_trial'].force_tap(10)
        sleep(2)
        while objects['battle'].tap(1):
            objects['set_out'].force_tap(10)
            objects['skip'].force_tap(10)
            objects['confirm_green'].force_tap(10)
            objects['ok'].force_tap(10)
            sleep(2)
        cls.close_ad()

    @classmethod
    def to_map(cls) -> None:
        """Goes to map from inside city"""
        cls.close_ad()
        objects["map"].force_tap()
        if not objects["book"].exists(10):
            cls.to_map()
            return
        sleep(1)
        reset_screen()

    def free_marches(self) -> int:
        """get number of available marches of current castle"""
        if not objects['book'].exists():
            log_raise("tried to check free marches while not at map")
        limit = self.marches
        if objects["more_marches"].tap():
            sleep(1)
        busy = objects["withdraw"].count() + objects["speed_up_march"].count()
        free = limit - busy
        logger.info(f"available {free}/{limit} marches")
        assert 0 <= free <= limit
        return free

    @staticmethod
    def withdraw() -> bool:
        if objects["withdraw"].tap(times=2, interval=1):
            objects["confirm_use_stamina"].force_tap(5)
            return True
        return False

    def kill_monster(self) -> None:
        if not self.stamina:
            return
        self.to_map()
        if self.free_marches() == 0:
            self.close_ad()
            return
        if objects["search"].tap():
            objects["monster"].force_exists(10)
        if objects["monster"].tap():
            if randrange(5) == 2:
                objects['monster_plus'].force_tap(10)
            objects["go"].force_exists(10)
        objects["go"].tap(times=5, interval=0.2)
        sleep(1)
        if not self.withdraw() and objects["arrow"].exists(2):
            objects["arrow"].force_tap(times=2, interval=0.2)
        for _ in range(30):
            if objects["quick_search"].tap():
                objects["map_hand"].force_tap(3)
                objects["arrow"].exists(2)
                objects["arrow"].tap(times=2, interval=0.5)

            elif objects['attack'].tap():
                objects["set_out"].tap(2)
                if objects["use_stamina"].tap(1):
                    objects["confirm_use_stamina"].force_tap(3)
                    back()
                    objects["set_out"].force_tap(3)
                    sleep(1.5)
                if not objects['book'].exists(1):
                    self.stamina = False
                break
            tap_center()
        self.close_ad()

    def _set_out(self) -> bool:
        if not objects['gather'].tap(4):
            return False

        if not objects['set_out'].exists(2):
            back()
            sleep(1)
            return False

        if objects['troops_slider'].count() == 6:
            self.is_enough_troops = False

        objects["set_out"].force_tap()

        if not objects['book'].exists(1):
            self.is_enough_troops = False
            back()
            sleep(1)
            return False

        return True

    def get_std_mine(self) -> None:
        """Gets standard mine from the map."""

        objects["search"].force_tap()
        for _ in range(24):
            level, need_type = next(self.mine_type)
            logger.info(f"searching mine. lv {level} {need_type.name.lower()}")
            need_type.value.force_tap(15)
            objects["plus"].tap(times=5)
            objects["minus"].tap(times=MAX_MINE_LEVEL - level)
            objects["go"].tap(times=4, interval=0.1)

            if objects["gather"].tap(4):
                self._set_out()
                print("mine taken.")
                self.mine_type = chain([(level, need_type)], self.mine_type)
                return
        log_raise(f"cannot find standard mine. check screen.png")

    def get_elite_mine(self) -> bool:
        """Gets elite mine from the map."""
        logger.info("Elite")
        objects["book"].force_tap()

        if objects["x_news"].tap(0.5):
            sleep(0.8)

        objects["elite_mines"].force_tap(4)
        sleep(1)

        if (
            not objects["blue"].exists(3)
            or (mines := objects["blue"].count()) == len(self.elite_mines_got)
        ):
            back()
            sleep(1)
            return False

        free = set(range(mines)) - self.elite_mines_got
        blue = choice(list(free))
        self.elite_mines_got.add(blue)

        objects["blue"].force_tap(index=blue)

        if not self._set_out():
            return self.get_elite_mine()

        return True

    def grow(self):
        self.bind_account()
        self.claim_rss()
        if self.last_login_minutes // 60 > 12:
            self.claim_mail()
            self.upgrade_lord_skills()
            self.pinata()
            self.events()
            self.claim_quest()
            if randrange(10) == 1:
                self.use_pack()
            self.join_alliance()
            self.alliance_rewards()
            while self.build():
                pass

        for i in range(100):
            logger.info(f"made {i} task. no_speed: {self.no_speed}")
            if i % 40 == 4:
                self.research()
                self.kill_monster()

            self.claim()
            self.heal()
            if not self.kingroad_task() or self.no_speed >= 4:
                break

        if self.level < 15:
            self.upgrade_castle()

        _ = self.marches
        self.to_map()
        if self.free_marches() != 0:
            self.get_elite_mine()
        while self.free_marches() >= 1 and self.is_enough_troops:
            self.get_std_mine()

        if not self.is_enough_troops:
            self.close_ad()
            self.recruit(horses=True)

        logger.info("don't know what to do in this castle.")
