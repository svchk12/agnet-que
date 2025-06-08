import React, { useCallback } from "react";
import { useDropzone } from "react-dropzone";

const dropzoneStyles = {
  border: "2px dashed #ccc",
  borderRadius: "8px",
  padding: "32px",
  textAlign: "center" as const,
  cursor: "pointer",
  transition: "border-color 0.3s ease",
};

const dropzoneActiveStyles = {
  borderColor: "#3b82f6",
};

const dropzoneTextStyles = {
  margin: 0,
  color: "#666",
  fontSize: "16px",
};

interface FileUploadProps {
  onUploadComplete: (jobId: string, filename: string) => void;
}

export const FileUpload: React.FC<FileUploadProps> = ({ onUploadComplete }) => {
  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (file) {
        try {
          const formData = new FormData();
          formData.append("file", file);

          const response = await fetch("http://localhost:8000/jobs", {
            method: "POST",
            body: formData,
          });

          if (!response.ok) {
            throw new Error("Failed to upload file");
          }

          const { jobId } = await response.json();
          console.log("Job created:", jobId);
          onUploadComplete(jobId, file.name);
        } catch (error) {
          console.error("Upload failed:", error);
        }
      }
    },
    [onUploadComplete]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "text/plain": [".txt"],
      "application/msword": [".doc"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        [".docx"],
    },
  });

  return (
    <div
      {...getRootProps()}
      style={{
        ...dropzoneStyles,
        ...(isDragActive ? dropzoneActiveStyles : {}),
      }}
    >
      <input {...getInputProps()} />
      <p style={dropzoneTextStyles}>
        {isDragActive
          ? "파일을 여기에 놓으세요..."
          : "파일을 드래그하거나 클릭하여 업로드하세요"}
      </p>
    </div>
  );
};
