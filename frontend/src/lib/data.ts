import fs from 'fs';
import path from 'path';

function sumColumn(filePath: string, columnName: string): number {
  try {
    const fullPath = process.cwd() + '/../' + filePath;
    if (!fs.existsSync(/*turbopackIgnore: true*/ fullPath)) return 0;
    
    const content = fs.readFileSync(/*turbopackIgnore: true*/ fullPath, 'utf8');
    const lines = content.split('\n');
    if (lines.length < 2) return 0;
    
    const headers = lines[0].split(',');
    const colIndex = headers.indexOf(columnName);
    if (colIndex === -1) return 0;
    
    let total = 0;
    for (let i = 1; i < lines.length; i++) {
      if (!lines[i].trim()) continue;
      const row = lines[i].match(/(".*?"|[^",\s]+)(?=\s*,|\s*$)/g) || lines[i].split(',');
      const val = parseFloat(row[colIndex]?.replace(/['"]/g, '') || "0");
      if (!isNaN(val)) total += val;
    }
    return total;
  } catch (e) {
    console.error(`Error reading ${filePath}`, e);
    return 0;
  }
}

function countRows(filePath: string): number {
  try {
    const fullPath = process.cwd() + '/../' + filePath;
    if (!fs.existsSync(/*turbopackIgnore: true*/ fullPath)) return 0;
    const content = fs.readFileSync(/*turbopackIgnore: true*/ fullPath, 'utf8');
    const lines = content.split('\n').filter(line => line.trim().length > 0);
    return Math.max(0, lines.length - 1);
  } catch (e) {
    console.error(`Error counting ${filePath}`, e);
    return 0;
  }
}

export function getMpladsMetrics() {
  const allocated = sumColumn('data/standardized/lok_sabha/allocation_standardized.csv', 'allocated_amount');
  const expenditure = sumColumn('data/standardized/lok_sabha/expenditure_standardized.csv', 'expenditure_amount');
  const completed = countRows('data/standardized/lok_sabha/completed_standardized.csv');
  const recommended = countRows('data/standardized/lok_sabha/recommended_standardized.csv');
  
  return {
    allocated,
    expenditure,
    completed,
    recommended,
  };
}

export function getTrendingProjects() {
  const fullPath = process.cwd() + '/../' + 'data/standardized/lok_sabha/recommended_standardized.csv';
  try {
    if (!fs.existsSync(/*turbopackIgnore: true*/ fullPath)) return [];
    
    const content = fs.readFileSync(/*turbopackIgnore: true*/ fullPath, 'utf8');
    const lines = content.split('\n').filter(line => line.trim().length > 0);
    if (lines.length < 2) return [];
    
    const headers = lines[0].split(',');
    const titleIdx = headers.indexOf('work_description');
    const amtIdx = headers.indexOf('recommended_amount');
    const locIdx = headers.indexOf('state');
    
    const projects = [];
    
    for (let i = 1; i < Math.min(4, lines.length); i++) {
      const cols = lines[i].split(/,(?=(?:(?:[^"]*"){2})*[^"]*$)/);
      const rawTitle = cols[titleIdx]?.replace(/^"|"$/g, '') || "--";
      projects.push({
        id: i,
        title: rawTitle,
        amount: parseFloat(cols[amtIdx]) || 0,
        status: "Recommended",
        location: cols[locIdx]?.replace(/^"|"$/g, '') || "--"
      });
    }
    
    return projects;
  } catch (e) {
    return [];
  }
}
