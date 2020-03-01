import jinja2
import os
from jinja2 import Template
from math import exp, ceil
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

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

        self.operations = [self.process_times[i] / self.process_fronts[i]
                           for i in range(self.operation_number)]

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

    def sequential_graphic(self):
        scale_x = 12 / self.time_sequential_prod_cycle
        plots = ''
        offset = 0
        for i in range(self.operation_number):
            plots += '\\draw[thick] (%f, %f) -- (%f, %f);' % (1 + offset * scale_x, self.operation_number - i + 1, 1 + (
                offset + parameters.processing_batch * parameters.process_times[i]) * scale_x, self.operation_number - i + 1)
            plots += '\\draw[thick,dotted] (%f, %f) -- (%f, %f);' % (1 + (offset + parameters.processing_batch * parameters.process_times[i]) * scale_x, self.operation_number - i + 1, 1 + (
                offset + parameters.processing_batch * parameters.process_times[i] + self.interoperational_break_sequential) * scale_x, self.operation_number - i + 1 - 1)
            offset = offset + parameters.processing_batch * \
                parameters.process_times[i] + \
                parameters.interoperational_break_sequential
        return plots

    def draw_sequential(self):
        plt.cla()
        

        fig, ax1 = plt.subplots()
        ax1.set_aspect('equal')
        ax1.xaxis.set_minor_locator(MultipleLocator(0.1))
        ax1.yaxis.set_minor_locator(MultipleLocator(0.1))
        ax1.xaxis.set_major_locator(MultipleLocator(1))
        ax1.yaxis.set_major_locator(MultipleLocator(1))
        ax1.xaxis.grid(True,'minor',linewidth=1)
        ax1.yaxis.grid(True,'minor',linewidth=1)
        ax1.xaxis.grid(True,'major',linewidth=2)
        ax1.yaxis.grid(True,'major',linewidth=2)
        offset = 0
        n_trans = self.processing_batch // self.transport_batch
        scale_x = 12 / self.time_sequential_prod_cycle
        scale_y = 1
        for i, op_len in enumerate(self.operations):
            y = len(self.operations) - i
            cyc_len = op_len * self.processing_batch

            x1 = offset
            x2 = x1 + cyc_len

            xx = np.asarray([x1 + op_len * self.transport_batch *
                             i for i in range(n_trans + 1)]) * scale_x
            ax1.plot(xx, np.asarray([y] * (n_trans + 1))
                     * scale_y, 'k-|', linewidth=2)
            if i != 0:
                ax1.plot(np.asarray([offset - self.interoperational_break_sequential, x1]) * scale_x,
                         np.asarray([y + 1, y]), 'k--', linewidth=2)
            offset += cyc_len + self.interoperational_break_sequential

        ax1.plot(np.asarray([offset - self.interoperational_break_sequential, offset]) * scale_x,
                 np.asarray([1, 0]) * scale_y, 'k--', linewidth=2)

        real_width = offset + self.interoperational_break_sequential
        real_height = len(self.operations) + 1

        ax1.axis([0, real_width * scale_x, 0, real_height * scale_y])
        ax1.set_yticklabels(['']*2 + [str(len(self.operations) - i) for i in range(len(self.operations))])

        ticks = ax1.get_xticks()
        xticks_labels = [''] * len(ticks)
        xticks_labels[1] = '0'
        xticks_labels[-2] = str(int(offset))
        ax1.set_xticklabels(xticks_labels)
        ax1.set_yticklabels(['']*2 + [str(len(self.operations) - i) for i in range(len(self.operations))])

        ticks = ax1.get_xticks()
        xticks_labels = [''] * len(ticks)
        xticks_labels[1] = '0'
        xticks_labels[-2] = str(int(offset))
        ax1.set_xticklabels(xticks_labels)
        plt.savefig('sequential.png', papertype='a4', dpi=400)
        return ''

    def draw_sequential_parallel(self):
        plt.cla()
        

        fig, ax1 = plt.subplots()
        ax1.set_aspect('equal')
        ax1.xaxis.set_minor_locator(MultipleLocator(0.1))
        ax1.yaxis.set_minor_locator(MultipleLocator(0.1))
        ax1.xaxis.set_major_locator(MultipleLocator(1))
        ax1.yaxis.set_major_locator(MultipleLocator(1))
        ax1.xaxis.grid(True,'minor',linewidth=1)
        ax1.yaxis.grid(True,'minor',linewidth=1)
        ax1.xaxis.grid(True,'major',linewidth=2)
        ax1.yaxis.grid(True,'major',linewidth=2)
        offset = 0
        xxlast = []
        
        n_trans = self.processing_batch // self.transport_batch
        scale_x = 12 / self.time_sequential_parallel_prod_cycle
        scale_y = 1
        for i, op_len in enumerate(self.operations):
            y = len(self.operations) - i
            xx = np.asarray([offset + op_len * self.transport_batch *
                             i for i in range(n_trans + 1)]) * scale_x
            ax1.plot(xx, np.asarray([y] * (n_trans + 1))
                     * scale_y, 'k-|', linewidth=2)

            if i != 0:
                xx_between = [np.asarray([a, b])
                              for a, b in zip(xxlast[1:], xx)]
                for xxb in xx_between:
                    ax1.plot(xxb, np.asarray([y + 1, y]), 'k--', linewidth=2)

            xxlast = xx
            if i + 1 != len(self.operations):
                if op_len < self.operations[i + 1]:
                    offset += op_len * self.transport_batch + self.interoperational_break_sequential_parallel  # from left
                else:
                    # from right
                    offset += (op_len * self.processing_batch) - \
                        (self.operations[i + 1] * self.transport_batch *
                         (n_trans - 1)) + self.interoperational_break_sequential_parallel
            else:
                offset += op_len * self.processing_batch + self.interoperational_break_sequential_parallel
        ax1.plot(np.asarray([offset - self.interoperational_break_sequential_parallel, offset]) * scale_x,
                 np.asarray([1, 0]) * scale_y, 'k--', linewidth=2)

        real_width = offset + self.interoperational_break_sequential_parallel
        real_height = len(self.operations) + 1

        ax1.axis([0, real_width * scale_x, 0, real_height * scale_y])
        ax1.set_yticklabels(['']*2 + [str(len(self.operations) - i) for i in range(len(self.operations))])

        ticks = ax1.get_xticks()
        xticks_labels = [''] * len(ticks)
        xticks_labels[1] = '0'
        xticks_labels[-2] = str(int(offset))
        ax1.set_xticklabels(xticks_labels)
        plt.savefig('sequential-parallel.png', papertype='a4', dpi=400)
        return ''

    def draw_parallel(self):
        plt.cla()
        

        fig, ax1 = plt.subplots()
        ax1.set_aspect('equal')
        ax1.xaxis.set_minor_locator(MultipleLocator(0.1))
        ax1.yaxis.set_minor_locator(MultipleLocator(0.1))
        ax1.xaxis.set_major_locator(MultipleLocator(1))
        ax1.yaxis.set_major_locator(MultipleLocator(1))
        ax1.xaxis.grid(True,'minor',linewidth=1)
        ax1.yaxis.grid(True,'minor',linewidth=1)
        ax1.xaxis.grid(True,'major',linewidth=2)
        ax1.yaxis.grid(True,'major',linewidth=2)
        
        offset = 0
        max_proc = max(self.operations)
        max_time = 0
        n_trans = self.processing_batch // self.transport_batch
        scale_x = 12 / self.time_sequential_parallel_prod_cycle
        scale_y = 1
        for j in range(n_trans):
            new_offset = 0
            max_reach = False
            for i, op_len in enumerate(self.operations):
                y = len(self.operations) - i
                if op_len != max_proc:
                    ax1.plot(np.asarray([offset, offset + op_len * self.transport_batch]) *
                             scale_x, np.asarray([y] * 2) * scale_y, 'k-|', linewidth=2)
                    if not max_reach:
                        new_offset -= op_len * self.transport_batch + self.interoperational_break_parallel
                else:
                    if j == 0:
                        xx = np.asarray(
                            [offset + op_len * self.transport_batch * i for i in range(n_trans + 1)]) * scale_x
                        ax1.plot(xx, np.asarray(
                            [y] * (n_trans + 1)) * scale_y, 'k-|', linewidth=2)
                    max_reach = True
                    new_offset += offset + op_len * self.transport_batch

                if i != 0:
                    ax1.plot(np.asarray([offset - self.interoperational_break_parallel, offset]) * scale_x,
                             np.asarray([y + 1, y]) * scale_y, 'k--', linewidth=2)
                offset += op_len * self.transport_batch + self.interoperational_break_parallel
            max_time = offset
            offset = new_offset

        ax1.plot(np.asarray([max_time - self.interoperational_break_parallel, max_time]) *
                 scale_x, np.asarray([1, 0]) * scale_y, 'k--', linewidth=2)

        real_width = max_time + self.interoperational_break_parallel
        real_height = len(self.operations) + 1

        ax1.axis([0, real_width * scale_x, 0, real_height * scale_y])
        ax1.set_yticklabels(['']*2 + [str(len(self.operations) - i) for i in range(len(self.operations))])

        ticks = ax1.get_xticks()
        xticks_labels = [''] * len(ticks)
        xticks_labels[1] = '0'
        xticks_labels[-2] = str(int(max_time))
        ax1.set_xticklabels(xticks_labels)
        plt.savefig('parallel.png', papertype='a4', dpi=400)
        return ''


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
