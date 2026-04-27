from datetime import datetime

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


def ensure_trainers_and_balance_workouts():
    changed = ensure_trainers()
    balanced = rebalance_workouts()
    if changed or balanced:
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


def _has_overlap(schedule, start_time, end_time):
    for scheduled_start, scheduled_end in schedule:
        if scheduled_end > start_time and scheduled_start < end_time:
            return True
    return False
