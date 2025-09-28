"""
Test correct France domain configuration
"""

from core.keepa_api import KeepaAPI
import inspect

def test_france_domain():
    """Test that we're using the correct domain for France"""
    
    print("🇫🇷 Testing France Domain Configuration")
    print("=" * 50)
    
    # Check default domain in get_product_data
    keepa_api = KeepaAPI("dummy_key")
    
    # Get the signature of get_product_data method
    signature = inspect.signature(keepa_api.get_product_data)
    domain_param = signature.parameters['domain']
    default_domain = domain_param.default
    
    print(f"📡 get_product_data default domain: {default_domain}")
    
    # Check default domain in get_price_history  
    signature_history = inspect.signature(keepa_api.get_price_history)
    domain_param_history = signature_history.parameters['domain']
    default_domain_history = domain_param_history.default
    
    print(f"📈 get_price_history default domain: {default_domain_history}")
    
    # Verify correct domains
    expected_domain = 4  # France
    
    if default_domain == expected_domain:
        print(f"✅ get_product_data: CORRECT (Domain {default_domain} = amazon.fr)")
    else:
        print(f"❌ get_product_data: WRONG (Domain {default_domain} ≠ {expected_domain})")
    
    if default_domain_history == expected_domain:
        print(f"✅ get_price_history: CORRECT (Domain {default_domain_history} = amazon.fr)")
    else:
        print(f"❌ get_price_history: WRONG (Domain {default_domain_history} ≠ {expected_domain})")
    
    # Domain reference
    print(f"\n🌍 Domain Reference:")
    print(f"   Domain 4 = amazon.fr (France) ✅")
    print(f"   Domain 8 = amazon.it (Italy) ❌")
    
    # Test what happens when we call the methods
    print(f"\n🧪 Method Call Test:")
    try:
        # This won't actually make an API call (no valid key), but we can see the setup
        print(f"   keepa_api.get_product_data('TEST123') will use domain: {default_domain}")
        print(f"   keepa_api.get_price_history('TEST123') will use domain: {default_domain_history}")
        
        if default_domain == 4 and default_domain_history == 4:
            print(f"   🎯 Result: All API calls will target FRANCE marketplace!")
        else:
            print(f"   ⚠️  Result: API calls may target wrong marketplace!")
            
    except Exception as e:
        print(f"   Note: {e}")
    
    return default_domain == expected_domain and default_domain_history == expected_domain

if __name__ == "__main__":
    success = test_france_domain()
    if success:
        print(f"\n🏁 SUCCESS: Configuration correctly targets France!")
    else:
        print(f"\n❌ FAILURE: Domain configuration needs fixing!")
