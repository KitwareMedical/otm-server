packages = c(
  "optparse",
  "png",
  "shape",
  "data.table",
  "lmvar",
  "stringr",
  "foreach",
  "doParallel",
  "RColorBrewer",
  "data.table",
  "pracma",
  "glmnet",
  "shiny",
  "mmand",
  "shinyBS",
  "broom",
  "markdown",
  "shiny",
  "corrplot",
  "shinyWidgets",
  "shinythemes",
  "shinyBS",
  "yaml",
  "raster",
  "DT",
  "RNifti"
)
install.packages(pkgs = packages)

deps <- c("devtools", "Rcpp", "RcppEigen", "magrittr", "rsvd", "magic", "psych")
install.packages(pkgs = deps, dependencies = TRUE)

library(devtools)
install_github("samuelgerber/msr")
install_github("samuelgerber/vtkwidgets")
install_github("samuelgerber/gmra")
install_github("girder/mop")

binaries = c(
  "https://github.com/stnava/ITKR/releases/download/v0.5.3.3.0/ITKR_0.5.3.3.0_R_x86_64-pc-linux-gnu_R4.1.tar.gz",
  "https://github.com/ANTsX/ANTsRCore/releases/download/v0.7.4.9/ANTsRCore_0.7.4.9_R_x86_64-pc-linux-gnu_R4.1.tar.gz",
  "https://github.com/ANTsX/ANTsR/releases/download/v0.5.7.4/ANTsR_0.5.7.4_R_x86_64-pc-linux-gnu_R4.1.tar.gz"
)
options(timeout=600) # allow more time for downloads to take place in the installation command below
install.packages(pkgs = binaries, repo = NULL)
