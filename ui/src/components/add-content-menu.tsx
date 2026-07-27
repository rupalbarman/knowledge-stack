import { useRef, useState, type ChangeEvent, type SubmitEvent } from "react";
import { Dialog, DropdownMenu } from "radix-ui";
import { FilePlus, FolderPlus, Plus } from "lucide-react";

import { fileHooks } from "@/hooks/file-hooks";
import { folderHooks } from "@/hooks/folder-hooks";

type AddContentMenuProps = {
  folderId: string | null;
};

export function AddContentMenu({ folderId }: AddContentMenuProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isFolderDialogOpen, setIsFolderDialogOpen] = useState(false);
  const [folderName, setFolderName] = useState("");

  const uploadFile = fileHooks.useUploadFile();
  const createFolder = folderHooks.useCreateFolder();

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    uploadFile.mutate({ file, folderId });
  }

  function handleCreateFolder(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    const name = folderName.trim();
    if (!name) return;

    createFolder.mutate(
      { name, parentId: folderId },
      {
        onSuccess: () => {
          setFolderName("");
          setIsFolderDialogOpen(false);
        },
      },
    );
  }

  return (
    <div className="flex items-center gap-2">
      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        onChange={handleFileChange}
      />

      <DropdownMenu.Root>
        <DropdownMenu.Trigger className="bg-primary text-primary-foreground inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium cursor-pointer">
          <Plus className="size-4" />
          New
        </DropdownMenu.Trigger>
        <DropdownMenu.Portal>
          <DropdownMenu.Content
            align="end"
            sideOffset={4}
            className="bg-popover text-popover-foreground border-border min-w-40 rounded-md border p-1 shadow-md"
          >
            <DropdownMenu.Item
              onSelect={() => fileInputRef.current?.click()}
              className="hover:bg-accent flex cursor-pointer items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-none"
            >
              <FilePlus className="size-4" />
              Upload file
            </DropdownMenu.Item>
            <DropdownMenu.Item
              onSelect={() => setIsFolderDialogOpen(true)}
              className="hover:bg-accent flex cursor-pointer items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-none"
            >
              <FolderPlus className="size-4" />
              New folder
            </DropdownMenu.Item>
          </DropdownMenu.Content>
        </DropdownMenu.Portal>
      </DropdownMenu.Root>

      {uploadFile.isError && (
        <p className="text-destructive text-xs">Upload failed</p>
      )}

      <Dialog.Root
        open={isFolderDialogOpen}
        onOpenChange={setIsFolderDialogOpen}
      >
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 bg-black/40" />
          <Dialog.Content className="bg-card text-card-foreground fixed top-1/2 left-1/2 w-80 -translate-x-1/2 -translate-y-1/2 rounded-md p-6 shadow-lg">
            <Dialog.Title className="text-base font-semibold">
              New folder
            </Dialog.Title>
            <form onSubmit={handleCreateFolder} className="mt-4 space-y-4">
              <input
                autoFocus
                value={folderName}
                onChange={(event) => setFolderName(event.target.value)}
                placeholder="Folder name"
                className="border-border w-full rounded-md border bg-transparent px-3 py-2 text-sm"
              />
              {createFolder.isError && (
                <p className="text-destructive text-sm">
                  Failed to create folder
                </p>
              )}
              <div className="flex justify-end gap-2">
                <Dialog.Close className="hover:bg-accent rounded-md px-3 py-1.5 text-sm">
                  Cancel
                </Dialog.Close>
                <button
                  type="submit"
                  disabled={createFolder.isPending}
                  className="bg-primary text-primary-foreground rounded-md px-3 py-1.5 text-sm font-medium disabled:opacity-50"
                >
                  {createFolder.isPending ? "Creating..." : "Create"}
                </button>
              </div>
            </form>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </div>
  );
}
