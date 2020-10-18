import sys
sys.path.append('../')

from pprint import pprint
from pyNTM import PerformanceModel

model = PerformanceModel.load_model_file('perf_model_lsp_metric.csv')

lsp_a_d_1 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_1')
lsp_a_d_2 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_2')

print("lsp_a_d_2 setup_bw = {}".format(lsp_a_d_2.configured_setup_bandwidth))
print("lsp_a_d_2 manual_metric = {}".format(lsp_a_d_2.manual_metric))
print()
print("lsp_a_d_1 setup_bw = {}".format(lsp_a_d_1.configured_setup_bandwidth))
print("lsp_a_d_1 manual_metric = {}".format(lsp_a_d_1.manual_metric))