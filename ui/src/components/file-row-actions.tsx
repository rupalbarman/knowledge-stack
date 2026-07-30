import { useRef, useState, type ChangeEvent } from "react";
import { Dialog, DropdownMenu } from "radix-ui";
import {
  ExternalLink,
  FileUp,
  MoreHorizontal,
  RefreshCw,
  Trash2,
} from "lucide-react";

import type { FileObject } from "@/common";
import { fileHooks } from "@/hooks/file-hooks";

type FileRowActionsProps = {
  file: FileObject;
  folderId: string | null;
};

export function FileRowActions({ file, folderId }: FileRowActionsProps) {
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const replaceInputRef = useRef<HTMLInputElement>(null);
  const getDownloadUrl = fileHooks.useGetDownloadUrl();
  const syncFile = fileHooks.useSyncFile();
  const deleteFile = fileHooks.useDeleteFile();
  const replaceFileContent = fileHooks.useReplaceFileContent();

  async function handleOpen() {
    const { url } = await getDownloadUrl.mutateAsync(file.id);
    window.open(url, "_blank");
  }

  function handleSync() {
    syncFile.mutate({ fileId: file.id, folderId });
  }

  function handleDelete() {
    deleteFile.mutate(
      { fileId: file.id, folderId },
      { onSuccess: () => setIsDeleteDialogOpen(false) },
    );
  }

  function handleReplaceFileChange(event: ChangeEvent<HTMLInputElement>) {
    const newFile = event.target.files?.[0];
    event.target.value = "";
    if (!newFile) return;
    replaceFileContent.mutate({ fileId: file.id, file: newFile, folderId });
  }

  return (
    <>
      <input
        ref={replaceInputRef}
        type="file"
        className="hidden"
        onChange={handleReplaceFileChange}
      />

      <DropdownMenu.Root>
        <DropdownMenu.Trigger
          className="hover:bg-accent cursor-pointer rounded-md p-1.5"
          aria-label="File actions"
        >
          <MoreHorizontal className="size-4" />
        </DropdownMenu.Trigger>
        <DropdownMenu.Portal>
          <DropdownMenu.Content
            align="end"
            sideOffset={4}
            className="bg-popover text-popover-foreground border-border min-w-40 rounded-md border p-1 shadow-md"
          >
            <DropdownMenu.Item
              onSelect={handleOpen}
              className="hover:bg-accent flex cursor-pointer items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-none"
            >
              <ExternalLink className="size-4" />
              Open
            </DropdownMenu.Item>
            <DropdownMenu.Item
              onSelect={handleSync}
              className="hover:bg-accent flex cursor-pointer items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-none"
            >
              <RefreshCw className="size-4" />
              Re-Sync
            </DropdownMenu.Item>
            <DropdownMenu.Item
              onSelect={() => replaceInputRef.current?.click()}
              className="hover:bg-accent flex cursor-pointer items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-none"
            >
              <FileUp className="size-4" />
              Replace content
            </DropdownMenu.Item>
            <DropdownMenu.Separator className="bg-border my-1 h-px" />
            <DropdownMenu.Item
              onSelect={() => setIsDeleteDialogOpen(true)}
              className="hover:bg-destructive/10 text-destructive flex cursor-pointer items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-none"
            >
              <Trash2 className="size-4" />
              Delete
            </DropdownMenu.Item>
          </DropdownMenu.Content>
        </DropdownMenu.Portal>
      </DropdownMenu.Root>

      {replaceFileContent.isError && (
        <p className="text-destructive text-xs">Failed to replace file</p>
      )}

      <Dialog.Root
        open={isDeleteDialogOpen}
        onOpenChange={setIsDeleteDialogOpen}
      >
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 bg-black/40" />
          <Dialog.Content className="bg-card text-card-foreground fixed top-1/2 left-1/2 w-80 -translate-x-1/2 -translate-y-1/2 rounded-md p-6 shadow-lg">
            <Dialog.Title className="text-base font-semibold">
              Delete "{file.name}"?
            </Dialog.Title>
            <p className="text-muted-foreground mt-2 text-sm">
              This permanently deletes the file and removes it from search.
              This can't be undone.
            </p>

            {deleteFile.isError && (
              <p className="text-destructive mt-2 text-sm">
                Failed to delete file
              </p>
            )}

            <div className="mt-4 flex justify-end gap-2">
              <Dialog.Close className="hover:bg-accent cursor-pointer rounded-md px-3 py-1.5 text-sm">
                Cancel
              </Dialog.Close>
              <button
                type="button"
                onClick={handleDelete}
                disabled={deleteFile.isPending}
                className="bg-destructive cursor-pointer rounded-md px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
              >
                {deleteFile.isPending ? "Deleting..." : "Delete"}
              </button>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </>
  );
}
