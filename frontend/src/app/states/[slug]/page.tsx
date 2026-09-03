import { redirect } from "next/navigation";

export default async function StateSlugRedirect({
  params,
  searchParams,
}: {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{ parliament?: string }>;
}) {
  const { slug } = await params;
  const { parliament } = await searchParams;
  const query = parliament ? `?parliament=${parliament}` : "";
  redirect(`/overview/state/${slug}${query}`);
}
