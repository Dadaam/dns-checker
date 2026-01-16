import sys
import dns.resolver
from src.models.graph import Node, NodeType
from src.strategies.ptr import PtrStrategy

def test_ptr_strategy():
    print("Testing PtrStrategy...")
    strategy = PtrStrategy()
    
    # Check if timeout is set
    if strategy.resolver.lifetime != 2.0:
        print("FAIL: Resolver lifetime not set to 2.0")
        sys.exit(1)
    else:
        print("PASS: Resolver lifetime is 2.0")

    # Test with a known IP (Google DNS) - should be fast
    node = Node(value="8.8.8.8", type=NodeType.IP_V4)
    print(f"Resolving {node.value}...")
    try:
        results = list(strategy.execute(node))
        for target, edge in results:
            print(f"  -> {target.value} ({edge.type})")
        print("PASS: Resolution successful")
    except Exception as e:
        print(f"ERROR: Resolution failed: {e}")

    # Test with an IP likely to timeout or fail (optional, difficult to guarantee timeout)
    # But mainly we want to ensure no BlockingIOError crash.

if __name__ == "__main__":
    test_ptr_strategy()
