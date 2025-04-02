"""
Young Aletheia

A module that adds child-like persona capabilities to Aletheia,
enabling interactions with a virtual child that learns and develops over time.
"""

__version__ = "0.1.0"

def initialize_young_aletheia(app=None):
    """
    Initialize the Young Aletheia system
    
    Args:
        app: Optional FastAPI application to integrate with
        
    Returns:
        YoungAletheiaIntegration instance or None if initialization failed
    """
    from young_aletheia.integration import YoungAletheiaIntegration
    
    try:
        # Create the integration
        integration = YoungAletheiaIntegration(app)
        
        print("✅ Young Aletheia initialized successfully")
        return integration
    except Exception as e:
        print(f"❌ Error initializing Young Aletheia: {e}")
        return None