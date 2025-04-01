def initialize_young_aletheia(app=None):
    """Initialize the Young Aletheia system"""
    from aletheia.young.integration import YoungAletheiaIntegration
    
    try:
        # Create the integration
        integration = YoungAletheiaIntegration(app)
        
        print("✅ Young Aletheia initialized successfully")
        return integration
    except Exception as e:
        print(f"❌ Error initializing Young Aletheia: {e}")
        return None