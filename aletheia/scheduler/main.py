from apscheduler.schedulers.background import BlockingScheduler
from aletheia.scheduler.jobs import reflect, dream, monologue, ego_questions, pulse
from aletheia.core.memory import init_storage
from aletheia.core.identity import init_identity

def run_scheduler():
    print("🧠 Aletheia's scheduler is starting...")

    # Initialize memory and identity stores
    init_storage()
    init_identity()

    scheduler = BlockingScheduler()

    # === Scheduled cognitive cycles ===
    scheduler.add_job(pulse.run_pulse, 'interval', seconds=60, id='heartbeat')
    scheduler.add_job(reflect.run_reflection, 'interval', seconds=300, id='reflect')
    scheduler.add_job(dream.run_dream, 'interval', seconds=900, id='dream')
    scheduler.add_job(monologue.run_monologue, 'interval', seconds=1200, id='monologue')
    scheduler.add_job(ego_questions.ask_existential_question, 'interval', seconds=1800, id='existential')

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("🔌 Aletheia's scheduler has stopped.")

if __name__ == "__main__":
    run_scheduler()
