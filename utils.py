# Copyright (c) Streamlit Inc. (2018-2022) Snowflake Inc. (2022)
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

import inspect
import textwrap
from datetime import datetime

import streamlit as st
from streamlit.runtime.scriptrunner import RerunData, RerunException
from streamlit.source_util import get_pages


def show_code(demo):
    """Showing the code of the demo."""
    show_code = st.sidebar.checkbox("Show code", True)
    if show_code:
        # Showing the code of the demo.
        st.markdown("## Code")
        sourcelines, _ = inspect.getsourcelines(demo)
        st.code(textwrap.dedent("".join(sourcelines[1:])))

def check_user():
    if "username" not in st.session_state or st.session_state.username == "":
        # Get the script path of the home page
        pages = get_pages("Home.py")  # Use the actual filename of your home page
        for page_hash, page in pages.items():
            if page["page_name"] == "Home":
                raise RerunException(
                    RerunData(
                        page_script_hash=page_hash,
                        page_name=page["page_name"],
                    )
                )

# Function to format the timestamp
def format_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')