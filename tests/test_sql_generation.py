

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test SQL generation with multiple models")
    parser.add_argument("--test", choices=["run", "execute"], default="run",
                       help="Test type: 'run' to execute tests, 'execute' to execute a bunch of SQL queries from a file")
    parser.add_argument("--mode", choices=["mysql", "text"], default="text",
                       help="Mode: 'mysql' for MySQL mode, 'base' for base mode")
    parser.add_argument("--db", default=False, help="Database name")
    parser.add_argument("--input", default=False, help="Input file with test requests")
    parser.add_argument("--output", default=False, help="Output file for results")
    parser.add_argument("--timeout", type=int, default=TIMEOUT_PER_MODEL,
                       help="Timeout per model per request (seconds)")
    
    args = parser.parse_args()
    
    if args.test == "run":        
        clear_tmp_dir(TMP_DIR)
        selected_db = select_test_database(args.db)

        input_file, output_dir = configure_run_paths(selected_db)
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"❌ Input file not found: {input_file}")

        # Update global variables based on args
        RUN_INPUT_FILE = args.input if args.input else input_file
        RUN_OUTPUT_DIR = args.output if args.output else output_dir
        TIMEOUT_PER_MODEL = args.timeout
        
        # Run the comprehensive tests
        run_stress_tests(args.mode, db_name=selected_db)
    else:
        raise ValueError(f"❌ Invalid test type: {args.test}")
