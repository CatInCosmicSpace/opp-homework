import jinja2
import os
from jinja2 import Template
from math import exp, ceil

latex_jinja_env = jinja2.Environment(
    block_start_string='\BLOCK{',
    block_end_string='}',
    variable_start_string='\VAR{',
    variable_end_string='}',
    comment_start_string='\#{',
    comment_end_string='}',
    line_statement_prefix='%%',
    line_comment_prefix='%#',
    trim_blocks=True,
    autoescape=True,
    loader=jinja2.FileSystemLoader(os.path.abspath('.')),
    extensions=['jinja2.ext.do']
)


class Parameters:
    def __init__(self, transport_batch, processing_batch, work_shift_duration, work_shift_number, process_times, process_fronts, interoperational_break_sequential, interoperational_break_sequential_parallel, interoperational_break_parallel):
        assert len(process_times) == len(process_fronts)
        self.transport_batch = transport_batch
        self.processing_batch = processing_batch

        self.process_times = process_times
        self.process_fronts = process_fronts
        self.operation_number = len(process_times)

        self.work_shift_duration = work_shift_duration
        self.work_shift_number = work_shift_number

        self.interoperational_break_sequential = interoperational_break_sequential
        self.interoperational_break_sequential_parallel = interoperational_break_sequential_parallel
        self.interoperational_break_parallel = interoperational_break_parallel

        self.sequentials = [(self.process_times[i], self.process_fronts[i])
                            for i in range(self.operation_number)]
        self.parallel_mins = [(self.process_times[i], self.process_fronts[i]) if self.process_times[i] / self.process_fronts[i] < self.process_times[i + 1] /
                              self.process_fronts[i + 1] else (self.process_times[i + 1], self.process_fronts[i + 1]) for i in range(self.operation_number - 1)]
        # print(self.parallel_mins)

        self.time_sequential_tech_cycle = round(
            self.processing_batch * sum([i[0] / i[1] for i in self.sequentials]))
        self.time_sequential_parallel_tech_cycle = round(self.time_sequential_tech_cycle - (
            self.processing_batch - self.transport_batch) * sum([i[0] / i[1] for i in self.parallel_mins]))

        max_time = max([self.process_times[i] / self.process_fronts[i]
                        for i in range(self.operation_number)])
        max_index = self.process_times.index(max_time)
        self.time_parallel_tech_cycle = round((self.processing_batch - self.transport_batch) * (
            self.process_times[max_index] / self.process_fronts[max_index]) + self.transport_batch * sum([i[0] / i[1] for i in self.sequentials]))

        self.time_sequential_prod_cycle = self.time_sequential_tech_cycle + \
            self.operation_number * self.interoperational_break_sequential
        self.time_sequential_parallel_prod_cycle = self.time_sequential_parallel_tech_cycle + \
            self.operation_number * self.interoperational_break_sequential_parallel
        self.time_parallel_prod_cycle = self.time_parallel_tech_cycle + \
            self.operation_number * self.interoperational_break_parallel

    def print_sum(self, sum_to_print):
        return '\\left(' + ''.join(['\\frac{%.1f}{%d}' % (sum_to_print[i][0], sum_to_print[i][1]) + (' + ' if i != (len(sum_to_print) - 1) else '') for i in range(len(sum_to_print))]) + '\\right)'

    def print_time_sequential_tech_cycle(self):
        return str(self.processing_batch) + '\\cdot ' + self.print_sum(self.sequentials)

    def print_time_sequential_parallel_tech_cycle(self):
        return self.print_time_sequential_tech_cycle() + ' - (%d - %d) \\cdot ' % (self.processing_batch, self.transport_batch) + self.print_sum(self.parallel_mins)

    def print_time_parallel_tech_cycle(self):
        max_time = max([self.process_times[i] / self.process_fronts[i]
                        for i in range(self.operation_number)])
        max_index = self.process_times.index(max_time)
        return '(%d - %d)' % (self.processing_batch, self.transport_batch) + '\\frac{%.1f}{%d}' % (self.process_times[max_index], self.process_fronts[max_index]) + ' + %d' % self.transport_batch + '\\cdot ' + self.print_sum(self.sequentials)


if __name__ == "__main__":
    parameters = Parameters(
        processing_batch=160,
        transport_batch=20,
        work_shift_duration=8,
        work_shift_number=2,
        process_times=[1.7, 2.9, 4.0, 3.3, 1.7, 3.7, 6.4, 1.0],
        process_fronts=[1, 1, 1, 1, 1, 2, 1, 1],
        interoperational_break_sequential=90,
        interoperational_break_sequential_parallel=30,
        interoperational_break_parallel=5
    )
    template = latex_jinja_env.get_template('main.tex.j2')
    with open('main.tex', 'wb') as file:
        file.write(template.render(parameters=parameters).encode('utf8'))
