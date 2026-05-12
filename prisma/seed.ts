import { PrismaClient } from "../src/generated/prisma/client";
import { PrismaBetterSqlite3 } from "@prisma/adapter-better-sqlite3";

const adapter = new PrismaBetterSqlite3({ url: "file:./dev.db" });
const prisma = new PrismaClient({ adapter });

async function main() {
  const categories = [
    { name: "Udělat", color: "#D47E30" },
    { name: "Vymyslet", color: "#4B6E48" },
    { name: "Naplánovat", color: "#AD9C8E" },
    { name: "Koupit", color: "#6F4E37" },
  ];

  for (const cat of categories) {
    await prisma.category.upsert({
      where: { name: cat.name },
      update: {},
      create: cat,
    });
  }

  console.log("Seed hotov – 4 default kategorie vytvořeny.");
}

main()
  .catch(console.error)
  .finally(() => prisma.$disconnect());
