#   Copyright (c) 2018 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
import numpy as np
import math
import sys
from op_test import OpTest


class TestROIPoolOp(OpTest):
    def set_data(self):
        self.init_test_case()
        self.make_rois()
        self.calc_roi_pool()

        self.inputs = {'X': self.x, 'ROIs': self.rois}

        self.attrs = {
            'spatial_scale': self.spatial_scale,
            'pooled_height': self.pooled_height,
            'pooled_width': self.pooled_width
        }

        self.outputs = {'Out': self.outs, 'Argmax': self.argmaxes}

    def init_test_case(self):
        self.batch_size = 5
        self.channels = 3
        self.height = 6
        self.width = 4

        # n, c, h, w
        self.x_dim = (self.batch_size, self.channels, self.height, self.width)

        self.spatial_scale = 1.0 / 4.0
        self.pooled_height = 2
        self.pooled_width = 2
        self.rois_num = 2

        self.x = np.random.random(self.x_dim).astype('float32')

    def calc_roi_pool(self):
        out_data = np.zeros((self.rois_num, self.channels, self.pooled_height,
                             self.pooled_width))
        argmax_data = np.zeros((self.rois_num, self.channels,
                                self.pooled_height, self.pooled_width))

        for i in range(self.rois_num):
            roi = self.rois[i]
            roi_batch_id = roi[0]
            roi_start_w = int(round(roi[1] * self.spatial_scale))
            roi_start_h = int(round(roi[2] * self.spatial_scale))
            roi_end_w = int(round(roi[3] * self.spatial_scale))
            roi_end_h = int(round(roi[4] * self.spatial_scale))

            roi_height = int(max(roi_end_h - roi_start_h + 1, 1))
            roi_width = int(max(roi_end_w - roi_start_w + 1, 1))

            x_i = self.x[roi_batch_id]

            bin_size_h = float(roi_height) / float(self.pooled_height)
            bin_size_w = float(roi_width) / float(self.pooled_width)

            for c in range(self.channels):
                for ph in range(self.pooled_height):
                    for pw in range(self.pooled_width):
                        hstart = int(math.floor(ph * bin_size_h))
                        wstart = int(math.floor(pw * bin_size_w))
                        hend = int(math.ceil((ph + 1) * bin_size_h))
                        wend = int(math.ceil((pw + 1) * bin_size_w))

                        hstart = min(max(hstart + roi_start_h, 0), self.height)
                        hend = min(max(hend + roi_start_h, 0), self.height)
                        wstart = min(max(wstart + roi_start_w, 0), self.width)
                        wend = min(max(wend + roi_start_w, 0), self.width)

                        is_empty = (hend <= hstart) or (wend <= wstart)
                        if is_empty:
                            out_data[i, c, ph, pw] = 0
                        else:
                            out_data[i, c, ph, pw] = -sys.float_info.max

                        argmax_data[i, c, ph, pw] = -1

                        for h in range(hstart, hend):
                            for w in range(wstart, wend):
                                if x_i[c, h, w] > out_data[i, c, ph, pw]:
                                    out_data[i, c, ph, pw] = x_i[c, h, w]
                                    argmax_data[i, c, ph, pw] = h * \
                                        self.width + w

        self.outs = out_data.astype('float32')
        self.argmaxes = argmax_data.astype('int64')

    def make_rois(self):
        rois = []
        batch_ids = np.random.randint(0, self.batch_size, size=self.rois_num)
        for i in range(self.rois_num):
            x1 = np.random.random_integers(
                0, self.width / self.spatial_scale - self.pooled_width)
            y1 = np.random.random_integers(
                0, self.height / self.spatial_scale - self.pooled_height)

            x2 = np.random.random_integers(x1 + self.pooled_width,
                                           self.width / self.spatial_scale)
            y2 = np.random.random_integers(y1 + self.pooled_height,
                                           self.height / self.spatial_scale)

            roi = [batch_ids[i], x1, y1, x2, y2]
            rois.append(roi)
        self.rois = np.array(rois).astype("int64")

    def setUp(self):
        self.op_type = "roi_pool"
        self.set_data()

    def test_check_output(self):
        self.check_output()

    def test_check_grad(self):
        self.check_grad(['X'], 'Out')


if __name__ == '__main__':
    unittest.main()