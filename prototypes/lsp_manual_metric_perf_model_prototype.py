import sys
sys.path.append('../')

from pprint import pprint
from pyNTM import PerformanceModel
from pyNTM import RSVP_LSP

model = PerformanceModel.load_model_file('perf_model_lsp_metric.csv')
model.update_simulation()

lsp_a_d_1 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_1')
lsp_a_d_2 = model.get_rsvp_lsp('A', 'D', 'lsp_a_d_2')

print("lsp_a_d_2 config_setup_bw = {}".format(lsp_a_d_2.configured_setup_bandwidth))
print("lsp_a_d_2 setup_bw = {}".format(lsp_a_d_2.setup_bandwidth))
print("lsp_a_d_2 manual_metric = {}".format(lsp_a_d_2.manual_metric))

print()
print("lsp_a_d_1 setup_bw = {}".format(lsp_a_d_1.configured_setup_bandwidth))
print("lsp_a_d_1 manual_metric = {}".format(lsp_a_d_1.manual_metric))
print("lsp_a_d_1 effective_metric = {}".format(lsp_a_d_1.effective_metric(model)))
print("lsp_a_d_1 topology_metric = {}".format(lsp_a_d_1.topology_metric(model)))

new_lsp = RSVP_LSP(model.get_node_object('A'), model.get_node_object('G'), 'lsp_a_f_manual_enter',
                   configured_setup_bandwidth=float('4'), configured_manual_metric=float('10'))
