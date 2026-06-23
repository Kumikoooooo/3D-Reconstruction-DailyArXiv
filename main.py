import sys
import time
import pytz
from datetime import datetime

from utils import get_daily_papers_by_keyword_with_retries, generate_table, back_up_files,\
    restore_files, remove_backups, get_daily_date


beijing_timezone = pytz.timezone('Asia/Shanghai')

# NOTE: arXiv API seems to sometimes return an unexpected empty list.

# get current beijing time date in the format of "2021-08-01"
current_date = datetime.now(beijing_timezone).strftime("%Y-%m-%d")
# get last update date from README.md
with open("README.md", "r") as f:
    while True:
        line = f.readline()
        if "Last update:" in line: break
    last_update_date = line.split(": ")[1].strip()
    # if last_update_date == current_date:
        # sys.exit("Already updated today!")

keywords = [
    # General 3D reconstruction
    "3D reconstruction",
    "multi-view reconstruction",
    "multi-view stereo",
    "structure from motion",
    "camera pose estimation",
    "depth estimation",
    "surface reconstruction",
    "mesh reconstruction",
    "point cloud reconstruction",

    # Neural rendering
    "neural rendering",
    "novel view synthesis",
    "radiance field",
    "NeRF",
    "neural surface reconstruction",
    "differentiable rendering",

    # Gaussian Splatting
    "Gaussian Splatting",
    "3D Gaussian Splatting",
    "Gaussian rasterization",
    "Gaussian surface reconstruction",

    # Density control and pruning
    "Gaussian densification",
    "Gaussian density control",
    "learnable density control",
    "Gaussian pruning",
    "Gaussian importance",
    "Gaussian contribution",
    "Gaussian uncertainty",
    "Gaussian merging",

    # Compression and acceleration
    "Gaussian compression",
    "compact Gaussian Splatting",
    "Gaussian quantization",
    "Gaussian entropy coding",
    "efficient Gaussian Splatting",
    "fast Gaussian Splatting",
    "real-time Gaussian Splatting",
    "Gaussian rendering acceleration",
    "level of detail Gaussian Splatting",

    # Feed-forward reconstruction
    "feed-forward 3D reconstruction",
    "feed-forward Gaussian Splatting",
    "generalizable Gaussian Splatting",
    "pose-free 3D reconstruction",
    "unposed image reconstruction",
    "geometry foundation model",
    "pointmap prediction",

    # Sparse view and active reconstruction
    "sparse-view reconstruction",
    "sparse-view Gaussian Splatting",
    "few-view Gaussian Splatting",
    "single-view reconstruction",
    "active view selection",
    "next best view",
    "uncertainty-guided view selection",

    # Large-scale and outdoor
    "large-scale 3D reconstruction",
    "large-scale Gaussian Splatting",
    "outdoor Gaussian Splatting",
    "city-scale reconstruction",
    "unbounded scene reconstruction",
    "hierarchical Gaussian Splatting",
    "multi-scale Gaussian Splatting",

    # Dynamic scene
    "dynamic Gaussian Splatting",
    "4D Gaussian Splatting",
    "deformable Gaussian Splatting",
    "dynamic scene reconstruction",
    "scene flow reconstruction",

    # SLAM
    "Gaussian Splatting SLAM",
    "Gaussian mapping",
    "online Gaussian Splatting",
    "RGB-D Gaussian SLAM",
    "LiDAR Gaussian SLAM",

    # Geometry and quality
    "geometry-aware Gaussian Splatting",
    "surface-aligned Gaussian Splatting",
    "mesh extraction from Gaussian Splatting",
    "anti-aliasing Gaussian Splatting",
    "frequency-aware Gaussian Splatting",
    "detail-preserving Gaussian Splatting",

    # Appearance and relighting
    "relightable Gaussian Splatting",
    "inverse rendering Gaussian Splatting",
    "BRDF Gaussian Splatting",
    "specular Gaussian Splatting",
    "reflection-aware Gaussian Splatting",
    "transparent Gaussian Splatting",

    # Semantics and editing
    "semantic Gaussian Splatting",
    "open-vocabulary Gaussian Splatting",
    "Gaussian Splatting segmentation",
    "language Gaussian Splatting",
    "Gaussian Splatting editing",
    "text-guided Gaussian editing",

    # Generative 3D
    "generative Gaussian Splatting",
    "text-to-3D Gaussian Splatting",
    "image-to-3D Gaussian Splatting",
    "diffusion Gaussian Splatting",

    # Multi-modal reconstruction
    "multi-modal 3D reconstruction",
    "LiDAR Gaussian Splatting",
    "event camera Gaussian Splatting",
    "thermal 3D reconstruction",
    "infrared Gaussian Splatting",
    "RGB-thermal reconstruction",

    # Humans and applications
    "human Gaussian Splatting",
    "Gaussian avatar",
    "autonomous driving Gaussian Splatting",
    "medical Gaussian Splatting",
] # TODO add more keywords

max_result = 100 # maximum query results from arXiv API for each keyword
issues_result = 15 # maximum papers to be included in the issue

# all columns: Title, Authors, Abstract, Link, Tags, Comment, Date
# fixed_columns = ["Title", "Link", "Date"]

column_names = ["Title", "Link", "Abstract", "Date", "Comment"]

back_up_files() # back up README.md and ISSUE_TEMPLATE.md

# write to README.md
f_rm = open("README.md", "w") # file for README.md
f_rm.write("# Daily Papers\n")
f_rm.write("The project automatically fetches the latest papers from arXiv based on keywords.\n\nThe subheadings in the README file represent the search keywords.\n\nOnly the most recent articles for each keyword are retained, up to a maximum of 100 papers.\n\nYou can click the 'Watch' button to receive daily email notifications.\n\nLast update: {0}\n\n".format(current_date))

# write to ISSUE_TEMPLATE.md
f_is = open(".github/ISSUE_TEMPLATE.md", "w") # file for ISSUE_TEMPLATE.md
f_is.write("---\n")
f_is.write("title: Latest {0} Papers - {1}\n".format(issues_result, get_daily_date()))
f_is.write("labels: documentation\n")
f_is.write("---\n")
f_is.write("**Please check the [Github](https://github.com/zezhishao/MTS_Daily_ArXiv) page for a better reading experience and more papers.**\n\n")

for keyword in keywords:
    f_rm.write("## {0}\n".format(keyword))
    f_is.write("## {0}\n".format(keyword))
    if len(keyword.split()) == 1: link = "AND" # for keyword with only one word, We search for papers containing this keyword in both the title and abstract.
    else: link = "OR"
    papers = get_daily_papers_by_keyword_with_retries(keyword, column_names, max_result, link)
    if papers is None: # failed to get papers
        print("Failed to get papers!")
        f_rm.close()
        f_is.close()
        restore_files()
        sys.exit("Failed to get papers!")
    rm_table = generate_table(papers)
    is_table = generate_table(papers[:issues_result], ignore_keys=["Abstract"])
    f_rm.write(rm_table)
    f_rm.write("\n\n")
    f_is.write(is_table)
    f_is.write("\n\n")
    time.sleep(5) # avoid being blocked by arXiv API

f_rm.close()
f_is.close()
remove_backups()
