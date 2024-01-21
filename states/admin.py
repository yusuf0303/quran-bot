from aiogram.dispatcher.filters.state import State, StatesGroup


class ADMIN(StatesGroup):
    start = State()
    main_menu = State()
