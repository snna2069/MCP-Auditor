"use client";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { InlineSpinner } from "@/components/shared/state-views";
import { useDeleteServer } from "@/hooks/use-servers";
import type { MCPServer } from "@/lib/types";
import { useState } from "react";

export function DeleteServerDialog({ server }: { server: MCPServer }) {
  const [open, setOpen] = useState(false);
  const { mutate, isPending } = useDeleteServer();

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger render={<Button variant="ghost" size="sm" />}>
        Delete
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete &ldquo;{server.name}&rdquo;?</DialogTitle>
          <DialogDescription>
            This removes the server registration and its discovered tools.
            Past audits are kept for historical reference. This cannot be
            undone.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button
            variant="destructive"
            disabled={isPending}
            onClick={() =>
              mutate(server.id, { onSuccess: () => setOpen(false) })
            }
          >
            {isPending ? <InlineSpinner label="Deleting..." /> : "Delete"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
