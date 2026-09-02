"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { ErrorState } from "@/components/shared/state-views";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useCreateServer } from "@/hooks/use-servers";

const formSchema = z.object({
  name: z.string().min(1, "Name is required").max(255),
  source_type: z.enum(["LOCAL_COMMAND", "HTTP", "MANUAL_CONFIGURATION"]),
  // LOCAL_COMMAND
  command: z.string().optional(),
  args: z.string().optional(),
  env: z.string().optional(),
  // HTTP
  url: z.string().optional(),
  headers: z.string().optional(),
  timeoutSeconds: z.string().optional(),
  // MANUAL_CONFIGURATION
  description: z.string().optional(),
  details: z.string().optional(),
});

type FormValues = z.infer<typeof formSchema>;

/** "KEY=value" or "KEY: value" per line -> a plain object. Blank lines and
 * lines without a separator are ignored, keeping this forgiving to type. */
function parseKeyValueLines(text: string | undefined): Record<string, string> {
  const result: Record<string, string> = {};
  for (const line of (text ?? "").split("\n")) {
    const match = line.match(/^\s*([^=:]+)\s*[:=]\s*(.*)\s*$/);
    if (match) {
      result[match[1].trim()] = match[2].trim();
    }
  }
  return result;
}

function buildConnectionConfig(
  values: FormValues,
): { config: Record<string, unknown> } | { error: string } {
  switch (values.source_type) {
    case "LOCAL_COMMAND": {
      if (!values.command?.trim()) {
        return { error: "Command is required for a local command server." };
      }
      return {
        config: {
          command: values.command.trim(),
          args: (values.args ?? "")
            .split(",")
            .map((a) => a.trim())
            .filter(Boolean),
          env: parseKeyValueLines(values.env),
        },
      };
    }
    case "HTTP": {
      if (!values.url?.trim()) {
        return { error: "URL is required for an HTTP server." };
      }
      const timeout = Number(values.timeoutSeconds || 30);
      return {
        config: {
          url: values.url.trim(),
          headers: parseKeyValueLines(values.headers),
          timeout_seconds: Number.isFinite(timeout) ? timeout : 30,
        },
      };
    }
    case "MANUAL_CONFIGURATION": {
      let details: Record<string, unknown> = {};
      if (values.details?.trim()) {
        try {
          details = JSON.parse(values.details);
        } catch {
          return { error: "Details must be valid JSON." };
        }
      }
      return {
        config: {
          description: values.description?.trim() || null,
          details,
        },
      };
    }
  }
}

export function NewServerForm() {
  const router = useRouter();
  const { mutate, isPending, isError, error } = useCreateServer();

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    setError,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: { source_type: "HTTP" },
  });

  const sourceType = watch("source_type");

  const onSubmit = (values: FormValues) => {
    const result = buildConnectionConfig(values);
    if ("error" in result) {
      setError("root", { message: result.error });
      return;
    }
    mutate(
      {
        name: values.name,
        source_type: values.source_type,
        connection_config: result.config,
      },
      { onSuccess: () => router.push("/servers") },
    );
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex max-w-lg flex-col gap-5">
      <div className="flex flex-col gap-1.5">
        <label htmlFor="name" className="text-sm font-medium">
          Name
        </label>
        <Input id="name" placeholder="weather-mcp" {...register("name")} />
        {errors.name && (
          <p className="text-sm text-destructive">{errors.name.message}</p>
        )}
      </div>

      <div className="flex flex-col gap-1.5">
        <label htmlFor="source_type" className="text-sm font-medium">
          Source type
        </label>
        <Select
          value={sourceType}
          onValueChange={(value) =>
            setValue(
              "source_type",
              value as "LOCAL_COMMAND" | "HTTP" | "MANUAL_CONFIGURATION",
            )
          }
        >
          <SelectTrigger id="source_type" className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="HTTP">HTTP</SelectItem>
            <SelectItem value="LOCAL_COMMAND">Local command</SelectItem>
            <SelectItem value="MANUAL_CONFIGURATION">
              Manual configuration
            </SelectItem>
          </SelectContent>
        </Select>
      </div>

      {sourceType === "HTTP" && (
        <>
          <div className="flex flex-col gap-1.5">
            <label htmlFor="url" className="text-sm font-medium">
              URL
            </label>
            <Input
              id="url"
              placeholder="https://example.com/mcp"
              {...register("url")}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor="headers" className="text-sm font-medium">
              Headers <span className="text-muted-foreground">(optional, one per line, KEY: value)</span>
            </label>
            <Textarea
              id="headers"
              placeholder={"Authorization: Bearer ..."}
              {...register("headers")}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor="timeoutSeconds" className="text-sm font-medium">
              Timeout (seconds)
            </label>
            <Input
              id="timeoutSeconds"
              type="number"
              placeholder="30"
              {...register("timeoutSeconds")}
            />
          </div>
        </>
      )}

      {sourceType === "LOCAL_COMMAND" && (
        <>
          <div className="flex flex-col gap-1.5">
            <label htmlFor="command" className="text-sm font-medium">
              Command
            </label>
            <Input id="command" placeholder="python" {...register("command")} />
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor="args" className="text-sm font-medium">
              Arguments{" "}
              <span className="text-muted-foreground">(optional, comma-separated)</span>
            </label>
            <Input id="args" placeholder="server.py, --port, 8080" {...register("args")} />
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor="env" className="text-sm font-medium">
              Environment variables{" "}
              <span className="text-muted-foreground">(optional, one per line, KEY=value)</span>
            </label>
            <Textarea id="env" placeholder={"API_KEY=..."} {...register("env")} />
          </div>
        </>
      )}

      {sourceType === "MANUAL_CONFIGURATION" && (
        <>
          <div className="flex flex-col gap-1.5">
            <label htmlFor="description" className="text-sm font-medium">
              Description <span className="text-muted-foreground">(optional)</span>
            </label>
            <Textarea
              id="description"
              placeholder="Documented via vendor PDF; no live connection."
              {...register("description")}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor="details" className="text-sm font-medium">
              Details JSON{" "}
              <span className="text-muted-foreground">
                (optional, e.g. {"{\"tools\": [...]}"})
              </span>
            </label>
            <Textarea
              id="details"
              placeholder='{"tools": []}'
              className="font-mono"
              {...register("details")}
            />
          </div>
        </>
      )}

      {errors.root && <ErrorState message={errors.root.message} />}
      {isError && (
        <ErrorState
          title="Could not create server"
          message={
            (error as { response?: { data?: { detail?: string } } })?.response
              ?.data?.detail ?? "Please check your input and try again."
          }
        />
      )}

      <div className="flex gap-2">
        <Button type="submit" disabled={isPending}>
          {isPending ? "Creating..." : "Create server"}
        </Button>
      </div>
    </form>
  );
}
