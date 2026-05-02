from datetime import datetime, timedelta

from models.database import db
from models.models import Trainer, Workout, WorkoutType


TRAINER_CATALOG = [
    {
        'first_name': 'Иван',
        'last_name': 'Петров',
        'experience_years': 8,
        'specialization': 'Силовые тренировки',
        'profile': 'Работает с базовой силой, набором мышечной массы и техникой упражнений.',
        'keywords': {'сил', 'body', 'pump', 'trx', 'функц'},
    },
    {
        'first_name': 'Мария',
        'last_name': 'Иванова',
        'experience_years': 9,
        'specialization': 'Йога и пилатес',
        'profile': 'Ведет мягкие и средние по нагрузке тренировки на мобильность, баланс и восстановление.',
        'keywords': {'йога', 'пилатес', 'стретч', 'каланет', 'bodyflex', 'лфк'},
    },
    {
        'first_name': 'Алексей',
        'last_name': 'Сидоров',
        'experience_years': 7,
        'specialization': 'Кроссфит и функциональный тренинг',
        'profile': 'Специализируется на интенсивных форматах, круговых тренировках и развитии выносливости.',
        'keywords': {'кросс', 'tabata', 'функц', 'trx'},
    },
    {
        'first_name': 'Екатерина',
        'last_name': 'Смирнова',
        'experience_years': 6,
        'specialization': 'Кардио и групповые программы',
        'profile': 'Ведет энергичные групповые форматы и помогает выстроить жиросжигающий тренировочный ритм.',
        'keywords': {'кардио', 'зумба', 'step', 'спин', 'танц', 'аэроб'},
    },
    {
        'first_name': 'Дмитрий',
        'last_name': 'Орлов',
        'experience_years': 10,
        'specialization': 'Боевые направления',
        'profile': 'Ставит технику, координацию и скоростно-силовую работу в боксе и тай-бо.',
        'keywords': {'бокс', 'тай'},
    },
    {
        'first_name': 'Анна',
        'last_name': 'Козлова',
        'experience_years': 5,
        'specialization': 'Женский фитнес и восстановление',
        'profile': 'Сочетает умеренную нагрузку, восстановительные практики и комфортный темп адаптации.',
        'keywords': {'пилатес', 'йога', 'стретч', 'лфк', 'аэроб'},
    },
]


AUTO_SCHEDULE_DAYS = 21
WEEKDAY_SLOTS = (7, 9, 12, 18, 20)
WEEKEND_SLOTS = (10, 12, 14, 16)
MAX_TRAINER_HOURS_PER_DAY = 6


def ensure_trainers_and_balance_workouts():
    changed = ensure_trainers()
    recurring = ensure_recurring_workout_schedule()
    scheduled = ensure_upcoming_workouts_for_all_trainers()
    covered_types = ensure_upcoming_workouts_for_all_types()
    balanced = rebalance_workouts()
    if changed or recurring or scheduled or covered_types or balanced:
        db.session.commit()


def ensure_trainers():
    changed = False
    for spec in TRAINER_CATALOG:
        trainer = Trainer.query.filter_by(
            first_name=spec['first_name'],
            last_name=spec['last_name'],
        ).first()

        if trainer is None:
            trainer = Trainer(
                first_name=spec['first_name'],
                last_name=spec['last_name'],
                experience_years=spec['experience_years'],
                specialization=spec['specialization'],
                profile=spec['profile'],
            )
            db.session.add(trainer)
            changed = True
        else:
            if trainer.experience_years != spec['experience_years']:
                trainer.experience_years = spec['experience_years']
                changed = True
            if trainer.specialization != spec['specialization']:
                trainer.specialization = spec['specialization']
                changed = True
            if trainer.profile != spec['profile']:
                trainer.profile = spec['profile']
                changed = True
    if changed:
        db.session.flush()
    return changed


def rebalance_workouts():
    trainers = Trainer.query.order_by(Trainer.id).all()
    workouts = Workout.query.join(WorkoutType).order_by(Workout.start_time, Workout.id).all()
    if not trainers or not workouts:
        return False

    trainer_meta = {
        trainer.id: next(
            (
                spec for spec in TRAINER_CATALOG
                if spec['first_name'] == trainer.first_name and spec['last_name'] == trainer.last_name
            ),
            None,
        )
        for trainer in trainers
    }
    trainer_loads = {trainer.id: 0 for trainer in trainers}
    trainer_schedule = {trainer.id: [] for trainer in trainers}
    changed = False

    for workout in workouts:
        workout_name = (workout.workout_type.name or '').lower()
        preferred = []
        fallback = []

        for trainer in trainers:
            if _has_overlap(trainer_schedule[trainer.id], workout.start_time, workout.end_time):
                continue

            meta = trainer_meta.get(trainer.id)
            if meta and any(keyword in workout_name for keyword in meta['keywords']):
                preferred.append(trainer)
            else:
                fallback.append(trainer)

        candidate_pool = preferred or fallback or trainers
        selected = min(candidate_pool, key=lambda trainer: (trainer_loads[trainer.id], trainer.id))

        if workout.trainer_id != selected.id:
            workout.trainer_id = selected.id
            changed = True

        trainer_loads[selected.id] += 1
        trainer_schedule[selected.id].append((workout.start_time, workout.end_time))

    return changed


def ensure_upcoming_workouts_for_all_trainers():
    trainers = Trainer.query.order_by(Trainer.id).all()
    workout_types = WorkoutType.query.order_by(WorkoutType.id).all()
    if not trainers or not workout_types:
        return False

    upcoming_workouts = (
        Workout.query.filter(Workout.start_time >= datetime.now())
        .order_by(Workout.start_time, Workout.id)
        .all()
    )
    changed = False

    for trainer in trainers:
        has_upcoming = any(workout.trainer_id == trainer.id for workout in upcoming_workouts)
        if has_upcoming:
            continue

        workout_type = _pick_workout_type_for_trainer(trainer, workout_types)
        if workout_type is None:
            continue

        start_time, end_time = _find_open_slot(trainer, upcoming_workouts)
        workout = Workout(
            trainer_id=trainer.id,
            workout_type_id=workout_type.id,
            start_time=start_time,
            end_time=end_time,
            max_participants=12,
            description=_build_generated_description(trainer, workout_type),
        )
        db.session.add(workout)
        upcoming_workouts.append(workout)
        changed = True

    if changed:
        db.session.flush()
    return changed


def ensure_upcoming_workouts_for_all_types():
    trainers = Trainer.query.order_by(Trainer.id).all()
    workout_types = WorkoutType.query.order_by(WorkoutType.id).all()
    if not trainers or not workout_types:
        return False

    upcoming_workouts = (
        Workout.query.filter(Workout.start_time >= datetime.now())
        .order_by(Workout.start_time, Workout.id)
        .all()
    )
    changed = False

    for workout_type in workout_types:
        has_upcoming = any(workout.workout_type_id == workout_type.id for workout in upcoming_workouts)
        if has_upcoming:
            continue

        trainer = _pick_trainer_for_workout_type(workout_type, trainers)
        start_time, end_time = _find_open_slot(trainer, upcoming_workouts)
        workout = Workout(
            trainer_id=trainer.id,
            workout_type_id=workout_type.id,
            start_time=start_time,
            end_time=end_time,
            max_participants=12,
            description=_build_generated_description(trainer, workout_type),
        )
        db.session.add(workout)
        upcoming_workouts.append(workout)
        changed = True

    if changed:
        db.session.flush()
    return changed


def ensure_recurring_workout_schedule(days_ahead=AUTO_SCHEDULE_DAYS):
    trainers = Trainer.query.order_by(Trainer.id).all()
    workout_types = WorkoutType.query.order_by(WorkoutType.id).all()
    if not trainers or not workout_types:
        return False

    now = datetime.now()
    start_day = now.date()
    horizon_end = now + timedelta(days=days_ahead)
    upcoming_workouts = (
        Workout.query.filter(
            Workout.start_time >= now,
            Workout.start_time < horizon_end,
        )
        .order_by(Workout.start_time, Workout.id)
        .all()
    )
    changed = False

    for day_offset in range(days_ahead):
        target_date = start_day + timedelta(days=day_offset)
        slots = WEEKEND_SLOTS if target_date.weekday() >= 5 else WEEKDAY_SLOTS

        for slot_index, hour in enumerate(slots):
            start_time = datetime.combine(target_date, datetime.min.time()).replace(hour=hour)
            end_time = start_time + timedelta(hours=1)
            if start_time <= now:
                continue

            workout_type = workout_types[(day_offset * len(slots) + slot_index) % len(workout_types)]
            if _has_existing_workout(upcoming_workouts, workout_type.id, start_time):
                continue

            trainer = _pick_available_trainer_for_slot(
                workout_type,
                trainers,
                upcoming_workouts,
                start_time,
                end_time,
            )
            if trainer is None:
                continue

            workout = Workout(
                trainer_id=trainer.id,
                workout_type_id=workout_type.id,
                start_time=start_time,
                end_time=end_time,
                max_participants=14,
                description=_build_recurring_description(trainer, workout_type),
            )
            db.session.add(workout)
            upcoming_workouts.append(workout)
            changed = True

    if changed:
        db.session.flush()
    return changed


def _has_overlap(schedule, start_time, end_time):
    for scheduled_start, scheduled_end in schedule:
        if scheduled_end > start_time and scheduled_start < end_time:
            return True
    return False


def _pick_workout_type_for_trainer(trainer, workout_types):
    meta = next(
        (
            spec for spec in TRAINER_CATALOG
            if spec['first_name'] == trainer.first_name and spec['last_name'] == trainer.last_name
        ),
        None,
    )
    if meta:
        keywords = meta['keywords']
        for workout_type in workout_types:
            workout_name = (workout_type.name or '').lower()
            if any(keyword in workout_name for keyword in keywords):
                return workout_type

    specialization = (trainer.specialization or '').lower()
    for workout_type in workout_types:
        workout_name = (workout_type.name or '').lower()
        if workout_name in specialization or specialization in workout_name:
            return workout_type

    return workout_types[trainer.id % len(workout_types)] if workout_types else None


def _pick_trainer_for_workout_type(workout_type, trainers):
    workout_name = (workout_type.name or '').lower()
    preferred = []

    for trainer in trainers:
        meta = next(
            (
                spec for spec in TRAINER_CATALOG
                if spec['first_name'] == trainer.first_name and spec['last_name'] == trainer.last_name
            ),
            None,
        )
        if meta and any(keyword in workout_name for keyword in meta['keywords']):
            preferred.append(trainer)

    pool = preferred or trainers
    return min(pool, key=lambda trainer: (len(trainer.workouts), trainer.id))


def _has_existing_workout(workouts, workout_type_id, start_time):
    return any(
        workout.workout_type_id == workout_type_id and workout.start_time == start_time
        for workout in workouts
    )


def _pick_available_trainer_for_slot(workout_type, trainers, workouts, start_time, end_time):
    day_start = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    workout_name = (workout_type.name or '').lower()
    candidates = []

    for trainer in trainers:
        trainer_workouts = [workout for workout in workouts if workout.trainer_id == trainer.id]
        trainer_schedule = [
            (workout.start_time, workout.end_time)
            for workout in trainer_workouts
        ]
        if _has_overlap(trainer_schedule, start_time, end_time):
            continue

        daily_hours = sum(
            (workout.end_time - workout.start_time).total_seconds() / 3600
            for workout in trainer_workouts
            if day_start <= workout.start_time < day_end
        )
        if daily_hours + 1 > MAX_TRAINER_HOURS_PER_DAY:
            continue

        meta = next(
            (
                spec for spec in TRAINER_CATALOG
                if spec['first_name'] == trainer.first_name and spec['last_name'] == trainer.last_name
            ),
            None,
        )
        preferred = bool(meta and any(keyword in workout_name for keyword in meta['keywords']))
        candidates.append((not preferred, daily_hours, len(trainer_workouts), trainer.id, trainer))

    if not candidates:
        return None

    return min(candidates)[-1]


def _find_open_slot(trainer, upcoming_workouts):
    trainer_workouts = [
        workout for workout in upcoming_workouts
        if workout.trainer_id == trainer.id
    ]
    trainer_schedule = [
        (workout.start_time, workout.end_time)
        for workout in trainer_workouts
    ]

    for day_offset in range(1, 15):
        for hour in (8, 10, 12, 14, 16, 18):
            start_time = datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(days=day_offset)
            start_time = start_time.replace(hour=hour)
            end_time = start_time + timedelta(hours=1)

            if _has_overlap(trainer_schedule, start_time, end_time):
                continue
            return start_time, end_time

    fallback_start = datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(days=21)
    fallback_start = fallback_start.replace(hour=10)
    return fallback_start, fallback_start + timedelta(hours=1)


def _build_generated_description(trainer, workout_type):
    return (
        f'Автоматически добавленная тренировка "{workout_type.name}" '
        f'для тренера {trainer.first_name} {trainer.last_name}.'
    )


def _build_recurring_description(trainer, workout_type):
    return (
        f'Регулярная тренировка "{workout_type.name}" '
        f'с тренером {trainer.first_name} {trainer.last_name}.'
    )
