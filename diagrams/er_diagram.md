# ER-диаграмма проекта Fitness Gym App

```mermaid
erDiagram
    USERS {
        INTEGER id PK
        VARCHAR_120 email UK
        VARCHAR_256 password_hash
        VARCHAR_50 first_name
        VARCHAR_50 last_name
        BOOLEAN is_admin
        DATETIME created_at
    }

    TRAINERS {
        INTEGER id PK
        VARCHAR_50 first_name
        VARCHAR_50 last_name
        INTEGER experience_years
        VARCHAR_100 specialization
        TEXT profile
    }

    WORKOUT_TYPES {
        INTEGER id PK
        VARCHAR_100 name UK
        TEXT description
    }

    WORKOUTS {
        INTEGER id PK
        INTEGER trainer_id FK
        INTEGER workout_type_id FK
        DATETIME start_time
        DATETIME end_time
        INTEGER max_participants
        TEXT description
    }

    BOOKINGS {
        INTEGER id PK
        INTEGER user_id FK
        INTEGER workout_id FK
        DATETIME booked_at
        BOOLEAN attended
        BOOLEAN visit_charged
    }

    ABONEMENTS {
        INTEGER id PK
        VARCHAR_100 name UK
        VARCHAR_50 type
        INTEGER price
        INTEGER duration_days
        INTEGER visits_count
        TEXT description
        TEXT features
        VARCHAR_20 color
        BOOLEAN is_popular
        INTEGER discount
        BOOLEAN is_active
        DATETIME created_at
    }

    USER_ABONEMENTS {
        INTEGER id PK
        INTEGER user_id FK
        INTEGER abonement_id FK
        DATETIME purchase_date
        DATETIME expiration_date
        INTEGER visits_remaining
        BOOLEAN is_active
        TEXT payment_info
    }

    USERS ||--o{ BOOKINGS : "создает записи"
    WORKOUTS ||--o{ BOOKINGS : "имеет записи"
    TRAINERS ||--o{ WORKOUTS : "проводит"
    WORKOUT_TYPES ||--o{ WORKOUTS : "классифицирует"
    USERS ||--o{ USER_ABONEMENTS : "покупает"
    ABONEMENTS ||--o{ USER_ABONEMENTS : "используется в"
```

## Связи

- `users.id` -> `bookings.user_id`: один пользователь может иметь много записей на тренировки.
- `workouts.id` -> `bookings.workout_id`: одна тренировка может иметь много записей.
- `trainers.id` -> `workouts.trainer_id`: один тренер проводит много тренировок.
- `workout_types.id` -> `workouts.workout_type_id`: один тип тренировки используется во многих тренировках.
- `users.id` -> `user_abonements.user_id`: один пользователь может купить много абонементов.
- `abonements.id` -> `user_abonements.abonement_id`: один тариф абонемента может быть куплен многими пользователями.
