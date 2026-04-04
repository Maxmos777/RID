import { useGetDownloadFileV2 } from "@/controllers/API/queries/file-management";
import type { FileType } from "@/types/file_management";

export const useCustomHandleSingleFileDownload = (file: FileType) => {
  const { mutate: downloadFile } = useGetDownloadFileV2({
    id: file.id,
    filename: file.name,
    type: file.path.split(".").pop() || "",
  });

  const handleSingleDownload = () => { downloadFile(); };

  return { handleSingleDownload };
};
