import { ArrowRight, IndianRupee, Briefcase, FileText, CheckCircle2 } from "lucide-react";
import { getMpladsMetrics, getTrendingProjects } from "@/lib/data";

export default async function Home() {
  const summaryData = getMpladsMetrics();
  const trendingProjects = getTrendingProjects();

  const formatCurrency = (val: number) => {
    if (val >= 10000000) return `₹${(val / 10000000).toFixed(2)} Cr`;
    if (val >= 100000) return `₹${(val / 100000).toFixed(2)} L`;
    return `₹${val.toLocaleString()}`;
  };

  return (
    <div className="flex flex-col gap-12 font-body pb-20">
      
      {/* Hero Section */}
      <section className="bg-surface rounded-xl p-8 md:p-12 shadow-medium border border-gray-100 relative overflow-hidden group">
        <div className="relative z-10 max-w-2xl">
          <h1 className="font-headline font-extrabold text-5xl md:text-6xl text-gray-900 leading-[1.1] tracking-tight mb-4">
            Monitoring India's Progress, <span className="text-primary">Real-time.</span>
          </h1>
          <p className="text-lg md:text-xl text-gray-600 mb-8 max-w-xl">
            Track MPLADS fund utilization, discover local development works, and ensure transparent progress across every constituency.
          </p>
          <button className="bg-primary hover:bg-[var(--color-primary-hover)] active:bg-[var(--color-primary-active)] text-white font-bold py-3 px-8 rounded-full text-lg transition-colors flex items-center gap-2">
            Explore All Projects <ArrowRight className="w-5 h-5" />
          </button>
        </div>
        {/* Decorative elements */}
        <div className="absolute right-[-10%] top-[-20%] w-96 h-96 bg-tertiary/20 rounded-full blur-3xl group-hover:bg-tertiary/30 transition-all duration-700" />
        <div className="absolute right-[10%] bottom-[-20%] w-80 h-80 bg-secondary/20 rounded-full blur-3xl group-hover:bg-secondary/30 transition-all duration-700" />
      </section>

      {/* Metrics Grid */}
      <section>
        <div className="flex items-center justify-between mb-6">
          <h2 className="font-headline font-bold text-3xl text-gray-900">National Overview</h2>
          <span className="text-sm font-bold text-primary tracking-wide uppercase">Live Data</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          
          <div className="bg-surface p-6 rounded-lg shadow-subtle border border-gray-100 hover:shadow-medium hover:-translate-y-1 transition-all duration-200">
            <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mb-4 text-primary">
              <IndianRupee className="w-6 h-6" />
            </div>
            <p className="text-gray-500 font-medium text-sm">Total Allocated</p>
            <h3 className="font-headline font-bold text-3xl text-gray-900 mt-1">{formatCurrency(summaryData.allocated)}</h3>
          </div>

          <div className="bg-surface p-6 rounded-lg shadow-subtle border border-gray-100 hover:shadow-medium hover:-translate-y-1 transition-all duration-200">
            <div className="w-12 h-12 bg-secondary/10 rounded-full flex items-center justify-center mb-4 text-secondary">
              <Briefcase className="w-6 h-6" />
            </div>
            <p className="text-gray-500 font-medium text-sm">Total Expenditure</p>
            <h3 className="font-headline font-bold text-3xl text-gray-900 mt-1">{formatCurrency(summaryData.expenditure)}</h3>
          </div>

          <div className="bg-surface p-6 rounded-lg shadow-subtle border border-gray-100 hover:shadow-medium hover:-translate-y-1 transition-all duration-200">
            <div className="w-12 h-12 bg-tertiary/20 rounded-full flex items-center justify-center mb-4 text-yellow-600">
              <FileText className="w-6 h-6" />
            </div>
            <p className="text-gray-500 font-medium text-sm">Recommended Works</p>
            <h3 className="font-headline font-bold text-3xl text-gray-900 mt-1">{summaryData.recommended.toLocaleString()}</h3>
          </div>

          <div className="bg-surface p-6 rounded-lg shadow-subtle border border-gray-100 hover:shadow-medium hover:-translate-y-1 transition-all duration-200">
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mb-4 text-green-600">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <p className="text-gray-500 font-medium text-sm">Completed Works</p>
            <h3 className="font-headline font-bold text-3xl text-gray-900 mt-1">{summaryData.completed.toLocaleString()}</h3>
          </div>

        </div>
      </section>

      {/* Trending Projects */}
      <section>
        <div className="flex items-center justify-between mb-6">
          <h2 className="font-headline font-bold text-3xl text-gray-900">Trending Projects</h2>
          <button className="text-primary font-semibold hover:text-[var(--color-primary-hover)] transition-colors">
            View all
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {trendingProjects.map((project) => (
            <div key={project.id} className="bg-surface rounded-lg border border-gray-200 overflow-hidden hover:shadow-[var(--shadow-product-hover)] hover:-translate-y-1 transition-all duration-300 flex flex-col h-full cursor-pointer">
              {/* Fake Image Placeholder */}
              <div className="h-48 bg-gray-100 relative">
                <div className="absolute inset-0 bg-gradient-to-tr from-gray-200 to-gray-50" />
                <div className="absolute top-4 left-4">
                  {project.status === "Completed" && (
                    <span className="bg-green-100 text-green-800 text-xs font-bold px-2 py-1 rounded-sm uppercase tracking-wider">
                      {project.status}
                    </span>
                  )}
                  {project.status === "In Progress" && (
                    <span className="bg-blue-100 text-blue-800 text-xs font-bold px-2 py-1 rounded-sm uppercase tracking-wider">
                      {project.status}
                    </span>
                  )}
                  {project.status === "Recommended" && (
                    <span className="bg-yellow-100 text-yellow-800 text-xs font-bold px-2 py-1 rounded-sm uppercase tracking-wider">
                      {project.status}
                    </span>
                  )}
                </div>
              </div>
              
              <div className="p-5 flex flex-col flex-grow">
                <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-1">{project.location}</p>
                <h3 className="font-headline font-bold text-xl text-gray-900 leading-tight mb-2 flex-grow">{project.title}</h3>
                
                <div className="flex items-center justify-between mt-4">
                  <div>
                    <p className="text-xs text-gray-500 font-medium">Allocated Amount</p>
                    <p className="font-bold text-secondary text-lg">₹{(project.amount / 100000).toFixed(1)} L</p>
                  </div>
                  
                  <button className="bg-primary hover:bg-[var(--color-primary-hover)] text-white p-2 rounded-full shadow-md transition-colors">
                    <ArrowRight className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

    </div>
  );
}
