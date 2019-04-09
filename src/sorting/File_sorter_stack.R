require(stringr)
setwd("/media/jonas/DATADISK1/XX_VM_shared_folder/01_IncuCyte/JM_002/")


filename.list <- list.files(path = "./Phase")
filename.chr <- as.character(filename.list)
filename.chr

wells<- stringr::str_match(string = filename.chr, pattern = "VID[0-9]{3}_([A-Z][0-9]{1,2})_1\\.tif")
well.names <- unique(wells[,2])
well.names


output_folder <- "./Full_sorted"

dir.create(path = output_folder, showWarnings = FALSE)

for (i in well.names) {
  dir.create(path = paste0(output_folder,"/",i,"/Red"), recursive = TRUE)
  dir.create(path = paste0(output_folder,"/",i,"/Phase"), recursive = TRUE)
  
  file.name.temp <- wells[wells[,2]==i,1]
  
  file.copy(from = paste0("./Phase/",file.name.temp), to = paste0(output_folder,"/", i, "/Phase/"), copy.mode = TRUE, copy.date = TRUE)
  file.copy(from = paste0("./Red/",file.name.temp), to = paste0(output_folder,"/", i, "/Red/"), copy.mode = TRUE, copy.date = TRUE)
  
}



#file.copy(from = paste0("./Phase/",wells[wells[,2]=="B4",1]), to = paste0("./Wells/", "B4", "/Phase/"), copy.mode = TRUE, copy.date = TRUE)

