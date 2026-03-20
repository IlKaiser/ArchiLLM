import os
import subprocess

PROJECTS_DIR = os.path.join("projects")

java_code = """package tescav;

import testing.MainTesting;
import testing.Model;
import java.lang.reflect.Field;
import java.io.FileWriter;
import java.io.PrintWriter;

public class DumpTestCases {
    public static void main(String[] args) throws Exception {
        Model model = new Model();
        
        Field modelField = MainTesting.class.getDeclaredField("model");
        modelField.setAccessible(true);
        modelField.set(null, model);
        
        MainTesting.makeModel("model.mxp");
        
        MainTescav tescav = new MainTescav(model);
        tescav.createObjects();
        tescav.endObjects();
        tescav.allTransitions();
        tescav.allLoopFreePaths();
        tescav.allOneLoopPaths();
        tescav.allStates();
        tescav.associationsEndMultiplicity();
        tescav.generalization();
        tescav.allTransitionPairs();
        tescav.allLoops();
        tescav.allMethods();
        
        Coverage coverage = tescav.getCoverage();
        
        try (PrintWriter out = new PrintWriter(new FileWriter(args[0]))) {
            out.println("<html><head><style>body { font-family: sans-serif; }</style></head><body><h1>Tescav Test Cases for " + args[1] + "</h1>");
            for (int i=0; i < coverage.getCriteriaSize(); i++) {
                out.println("<h2>" + coverage.getCriterionName(i) + "</h2>");
                out.println(coverage.getCriterionHelpText(i));
                out.println("<hr>");
            }
            out.println("</body></html>");
        }
    }
}
"""

import glob

merode_dirs = glob.glob(os.path.join(PROJECTS_DIR, "**", "merode_application"), recursive=True)

for merode_dir in merode_dirs:
    project = os.path.basename(os.path.dirname(merode_dir))

    print(f"Processing project: {project}")
    
    # Write the java file
    tescav_dir = os.path.join(merode_dir, "src", "tescav")
    dump_file = os.path.join(tescav_dir, "DumpTestCases.java")
    with open(dump_file, "w") as f:
        f.write(java_code)

    # Compile the java file
    compile_cmd = ['javac', '-cp', 'bin:lib/*:lib/hibernate3-jars/*', '-d', 'bin', 'src/tescav/DumpTestCases.java']
    compile_result = subprocess.run(compile_cmd, cwd=merode_dir, capture_output=True, text=True)
    if compile_result.returncode != 0:
        print(f"Compilation failed for {project}")
        print(compile_result.stderr)
        continue

    # Execute the java file
    html_output = f"{project}_testcases.html"
    execute_cmd = ['java', '-cp', 'bin:lib/*:lib/hibernate3-jars/*', 'tescav.DumpTestCases', html_output, project]
    execute_result = subprocess.run(execute_cmd, cwd=merode_dir, capture_output=True, text=True)
    if execute_result.returncode != 0:
        print(f"Execution failed for {project}")
        print(execute_result.stderr)
        continue
        
    print(f"Successfully generated {html_output} in {merode_dir}")
