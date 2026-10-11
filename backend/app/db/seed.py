"""Local-only database seeding script for development and demonstration."""

import os
import sys
from backend.app.core.config import settings
from backend.app.db.session import SessionLocal
from backend.app.models.user import User
from backend.app.models.trial import Trial
from backend.app.core.security import hash_password, normalize_email
from backend.app.services.audit_service import (
    record_audit_event,
    ACTION_AUTH_REGISTER,
    ACTION_TRIAL_CREATE,
)


def seed_demo_data() -> None:
    """Seed a local demo user and initial trial. Disallowed in production."""
    if settings.APP_ENV == "production":
        print("ERROR: Demo user seeding is strictly prohibited in production environments.", file=sys.stderr)
        sys.exit(1)

    demo_email = normalize_email(os.getenv("DEMO_USER_EMAIL", "demo@trialanalytics.local"))
    demo_password = os.getenv("DEMO_USER_PASSWORD", "DemoPass123!")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == demo_email).first()
        if user:
            print(f"[Seed] Demo user '{demo_email}' already exists (ID: {user.id}).")
        else:
            user = User(
                email=demo_email,
                password_hash=hash_password(demo_password),
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            record_audit_event(
                db=db,
                action=ACTION_AUTH_REGISTER,
                entity_type="user",
                entity_id=user.id,
                actor_user_id=user.id,
                outcome="success",
                metadata={"email": demo_email, "is_seeded_demo": True},
            )
            print(f"[Seed] Successfully created demo user '{demo_email}' (ID: {user.id}).")

        # Check or create starter demo trial
        trial = (
            db.query(Trial)
            .filter(Trial.owner_user_id == user.id, Trial.trial_code == "DEMO-001")
            .first()
        )
        if trial:
            print(f"[Seed] Demo trial 'DEMO-001' already exists (ID: {trial.id}).")
        else:
            trial = Trial(
                owner_user_id=user.id,
                trial_code="DEMO-001",
                trial_name="Cardiovascular Synthetic Trial Phase 2",
                status="active",
            )
            db.add(trial)
            db.commit()
            db.refresh(trial)

            record_audit_event(
                db=db,
                action=ACTION_TRIAL_CREATE,
                entity_type="trial",
                entity_id=trial.id,
                actor_user_id=user.id,
                outcome="success",
                metadata={"trial_code": "DEMO-001"},
            )
            print(f"[Seed] Successfully created demo trial 'DEMO-001' (ID: {trial.id}).")

    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
