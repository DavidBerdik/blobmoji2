# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Post-process Noto-COLRv0 fonts after nanoemoji."""

from absl import app

from colrv1_postproc import _COLRV0_FILES, _main_colr_files


def main(_):
    _main_colr_files(_COLRV0_FILES, 0)


if __name__ == "__main__":
    app.run(main)