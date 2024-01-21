from aiogram.dispatcher.filters.state import State, StatesGroup


class USER(StatesGroup):
    start = State()
    main_menu = State()
    region = State()
    region_callback = State()
    day_parts = State()
    week_times = State()
