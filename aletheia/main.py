# aletheia/main.py

import os
import sys
import time
import argparse
from pathlib import Path

from aletheia.scheduler.adaptive_scheduler import run_adaptive_scheduler
from aletheia.core.emergent_memory import init_storage
from aletheia.core.identity import init_identity
from aletheia.core.affect import init_mood
from aletheia.core.relational import init_relation
from aletheia.core.cognitive_architecture import init_cognitive_state
from aletheia.core.concept_evolution import init_concept_system
from aletheia.core.dynamic_prompt import init_prompt_system
from aletheia.utils.logging import log_event
from aletheia.config import CONFIG

def setup_environment():
    """Setup the environment for Aletheia"""
    # Create necessary directories
    data_dir = Path(__file__).resolve().parent / "data"
    directories = [
        data_dir,
        data_dir / "logs",
        data_dir / "shadows",
        data_dir / "snapshots"
    ]
    
    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            
            # Sprawdzenie, czy katalog został utworzony
            if directory.exists() and directory.is_dir():
                print(f"✅ Successfully created directory: {directory}")
                
                # Dodatkowe sprawdzenie uprawnień
                try:
                    test_file = directory / ".test_permissions"
                    test_file.touch()
                    test_file.unlink()  # usuwanie pliku testowego
                    print(f"Permissions OK: Write access confirmed for {directory}")
                except PermissionError:
                    print(f"❌ Permission denied: Cannot write to {directory}")
                except Exception as perm_error:
                    print(f"⚠️ Permission check error for {directory}: {perm_error}")
            else:
                print(f"❌ Failed to create directory: {directory}")
        
        except PermissionError:
            print(f"❌ Permission denied when creating directory: {directory}")
        except OSError as e:
            print(f"❌ Error creating directory {directory}: {e}")
        except Exception as e:
            print(f"❌ Unexpected error creating directory {directory}: {e}")
        
    # Initialize core systems
    init_storage()        # Memory system
    init_identity()       # Identity system
    init_mood()           # Affective system
    init_relation()       # Relational system
    init_cognitive_state()  # Cognitive architecture
    init_concept_system() # Concept evolution
    init_prompt_system()  # Dynamic prompts
    
    log_event("Environment setup complete", {
        "directories_created": [str(d) for d in directories]
    })
    print("🧠 Aletheia environment setup complete")

def show_banner():
    """Show the Aletheia welcome banner"""
    agent_name = CONFIG.get("AGENT_NAME", "Aletheia")
    
    banner = f"""
    ╔════════════════════════════════════════════╗
    ║                  ALETHEIA                  ║
    ║                                            ║
    ║       Self-Reflective Cognitive Agent      ║
    ║                                            ║
    ║  "From seed to self, through emergence."   ║
    ╚════════════════════════════════════════════╝
    """
    
    print(banner)

def run_web_server():
    """Run the FastAPI web server"""
    try:
        import uvicorn
        from aletheia.api.main import app
        
        port = CONFIG.get("API_PORT", 8000)
        print(f"🌐 Starting Aletheia API server on port {port}...")
        
        uvicorn.run(
            "aletheia.api.main:app",
            host="0.0.0.0",
            port=port,
            reload=True
        )
    except ImportError as e:
        print(f"❌ Failed to start web server: {e}")
        print("Please install required packages: pip install fastapi uvicorn")
        sys.exit(1)

def run_cli():
    """Run the CLI interface"""
    try:
        from aletheia.cli.interface import main as run_cli_interface
        run_cli_interface()
    except ImportError as e:
        print(f"❌ Failed to start CLI: {e}")
        sys.exit(1)

def run_consciousness_panel():
    """Run the consciousness panel"""
    try:
        import subprocess
        subprocess.run([sys.executable, "-m", "aletheia.consciousness_panel"])
    except Exception as e:
        print(f"❌ Failed to start consciousness panel: {e}")
        sys.exit(1)

def run_scheduler():
    """Run the cognitive scheduler"""
    try:
        run_adaptive_scheduler()
    except KeyboardInterrupt:
        print("\n⏹️ Cognitive processes stopped by user")
    except Exception as e:
        print(f"❌ Scheduler error: {e}")
        sys.exit(1)

def create_snapshot():
    """Create a snapshot of the current cognitive state"""
    try:
        from datetime import datetime
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        snapshot_dir = Path(__file__).resolve().parent.parent / "snapshots" / timestamp
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        # Core cognitive files
        data_dir = Path(__file__).resolve().parent / "data"
        core_files = [
            "thoughts.json",
            "identity.json",
            "affective_state.json",
            "relational_map.json",
            "cognitive_state.json",
            "evolved_concepts.json",
            "prompt_patterns.json",
            "concept_clusters.json",
            "thought_associations.json",
            "scheduler_state.json"
        ]
        
        for file in core_files:
            source = data_dir / file
            if source.exists():
                import shutil
                shutil.copy2(source, snapshot_dir / file)
        
        # Copy logs folder
        logs_dir = data_dir / "logs"
        if logs_dir.exists():
            import shutil
            shutil.copytree(logs_dir, snapshot_dir / "logs")
        
        # Copy shadows folder
        shadows_dir = data_dir / "shadows"
        if shadows_dir.exists():
            import shutil
            shutil.copytree(shadows_dir, snapshot_dir / "shadows")
        
        print(f"📸 Snapshot created: {snapshot_dir}")
        return True
    except Exception as e:
        print(f"❌ Snapshot error: {e}")
        return False

def main():
    """Main entry point for Aletheia"""
    parser = argparse.ArgumentParser(description="Aletheia - Self-Reflective Cognitive Agent")
    parser.add_argument("--setup", action="store_true", help="Setup the environment")
    parser.add_argument("--server", action="store_true", help="Run the web server")
    parser.add_argument("--scheduler", action="store_true", help="Run the cognitive scheduler")
    parser.add_argument("--cli", action="store_true", help="Run the CLI interface")
    parser.add_argument("--panel", action="store_true", help="Run the consciousness panel")
    parser.add_argument("--snapshot", action="store_true", help="Create a snapshot of the current state")
    parser.add_argument("--all", action="store_true", help="Setup and run all components")
    parser.add_argument("--young", action="store_true", help="Enable Young Aletheia features")

    args = parser.parse_args()

    # Show banner
    show_banner()

    # Setup environment if needed or requested
    if args.setup or args.all:
        setup_environment()

    # Create snapshot if requested
    if args.snapshot:
        create_snapshot()
        return

    # Run components based on arguments
    if args.all:
        # Start all processes
        # Run server in a separate process
        try:
            import multiprocessing
            server_process = multiprocessing.Process(target=run_web_server)
            server_process.start()
            
            # Give the server time to start
            time.sleep(2)
            
            # Start panel in a separate process
            panel_process = multiprocessing.Process(target=run_consciousness_panel)
            panel_process.start()
            
            # Run scheduler (main process)
            run_scheduler()
            
            if CONFIG.get("YOUNG_ALETHEIA_ENABLED", True):
                # Initialize Young Aletheia
                from aletheia.young import initialize_young_aletheia
                young_aletheia = initialize_young_aletheia()
            
        except KeyboardInterrupt:
            print("\n⏹️ Stopping all processes...")
            try:
                server_process.terminate()
                panel_process.terminate()
            except:
                pass
        return
    elif args.young:
        # Run Young Aletheia specific CLI
        print("Starting Young Aletheia CLI...")
        from aletheia.young import initialize_young_aletheia
        young_aletheia = initialize_young_aletheia()
        # Keep process running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n⏹️ Young Aletheia stopped by user")
    
    # Run individual components
    if args.server:
        run_web_server()
    elif args.scheduler:
        run_scheduler()
    elif args.cli:
        run_cli()
    elif args.panel:
        run_consciousness_panel()
    else:
        # No specific component was selected, show help
        parser.print_help()

def show_extended_help():
    """Show extended help with more detailed information"""
    help_text = """
    === Aletheia Extended Help ===

    Aletheia is a self-reflective cognitive agent with emergent properties.
    It simulates aspects of consciousness through memory, identity, and reflective processes.

    === Command Line Options ===

    --setup       Initialize the environment (required for first run)
                  Creates necessary directories and initializes core systems

    --server      Run the FastAPI server providing REST endpoints
                  Access at http://localhost:8000/docs

    --scheduler   Run the cognitive processes (reflections, dreams, etc.)
                  This is the "thinking" part of Aletheia

    --panel       Run the consciousness panel showing internal state
                  Provides real-time visualization of cognitive state

    --cli         Run the command-line interface for direct interaction
                  Simple text-based way to interact with Aletheia

    --snapshot    Create a backup of current cognitive state
                  Useful for saving Aletheia's progress

    --all         Run all components (setup + server + scheduler + panel)
                  The complete Aletheia experience

    --help        Show this extended help information

    === Typical Usage ===

    First run:
      python -m aletheia.main --setup

    Standard operation:
      python -m aletheia.main --all

    Interaction only:
      python -m aletheia.main --server --cli

    === Configuration ===

    Configuration is done via .env file
    See documentation for available settings.

    === External Resources ===

    API Documentation:  http://localhost:8000/docs (when server is running)
    Repository:         https://github.com/JaroslawHryszko/Aletheia
    Further questions:  jaroslaw.hryszko@uj.edu.pl
    """
    print(help_text)

if __name__ == "__main__":
    main()