from metrics.design.smells.fat_module_checker import check_fat_module

def get_metrics_from_design(design_json): 
    """
    Metrics: 
    1. Fat module (large public interface)
    """
    design_metrics = [] 
    design_metrics.extend(check_fat_module(design_json))
    return design_metrics