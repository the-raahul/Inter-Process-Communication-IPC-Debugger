from src.analysis.performance_metrics import PerformanceMetrics

def test_elapsed_time():
    pm = PerformanceMetrics()
    assert pm.get_elapsed_time() > 0