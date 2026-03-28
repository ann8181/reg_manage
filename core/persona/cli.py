#!/usr/bin/env python3
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from persona_system import PersonaSystem, create_persona_system

def cmd_generate(args):
    ps = create_persona_system(args.data_dir)
    
    if args.batch:
        identities = ps.generate_batch_identities(
            count=args.batch,
            country=args.country,
            gender=args.gender,
            age_range=(args.age_min, args.age_max)
        )
        print(f"Generated {len(identities)} identities")
        for identity in identities:
            print(f"  - {identity['id']}: {identity['profile']['name']['full']} (Score: {identity['quality_score']})")
    else:
        identity = ps.generate_identity(
            country=args.country,
            gender=args.gender,
            age_range=(args.age_min, args.age_max)
        )
        print(f"Generated Identity:")
        print(f"  ID: {identity['id']}")
        print(f"  Name: {identity['profile']['name']['full']}")
        print(f"  Gender: {identity['profile']['demographics']['gender']}")
        print(f"  Age: {identity['profile']['demographics']['age']}")
        print(f"  Location: {identity['profile']['location']['city']}, {identity['profile']['location']['state']}")
        print(f"  Quality Score: {identity['quality_score']}")

def cmd_list(args):
    ps = create_persona_system(args.data_dir)
    stats = ps.get_identity_stats()
    
    print(f"Total Identities: {stats['total']}")
    print(f"By Status: {stats['by_status']}")
    print(f"Quality Distribution: {stats['quality_distribution']}")

def cmd_stats(args):
    ps = create_persona_system(args.data_dir)
    all_stats = ps.get_system_stats()
    print("System Statistics:")
    print(f"  Identities: {all_stats['identities']['total']}")
    print(f"  Accounts: {all_stats['accounts']['total']}")
    print(f"  Proxies: {all_stats['proxies']['total']}")
    print(f"  Tasks: {all_stats['tasks']['total']}")

def cmd_create_account(args):
    ps = create_persona_system(args.data_dir)
    
    identity_id = args.identity_id
    if not identity_id:
        identity = ps.select_identity_for_service(args.service)
        if identity:
            identity_id = identity['id']
            print(f"Auto-selected identity: {identity_id}")
        else:
            print("No identity available")
            return
    
    credentials = {
        "email": args.email,
        "password": args.password,
        "username": args.username or ""
    }
    
    service_info = {
        "name": args.service,
        "display_name": args.service.upper(),
        "category": args.category or "other"
    }
    
    account = ps.create_account(
        identity_id=identity_id,
        service=service_info,
        credentials=credentials
    )
    
    print(f"Created Account:")
    print(f"  ID: {account['id']}")
    print(f"  Service: {account['service']['name']}")
    print(f"  Email: {account['credentials']['email']}")
    print(f"  Identity: {account['identity_id']}")

def cmd_add_proxy(args):
    ps = create_persona_system(args.data_dir)
    
    proxy = ps.add_proxy(
        host=args.host,
        port=args.port,
        protocol=args.protocol,
        username=args.username,
        password=args.password,
        country=args.country
    )
    
    print(f"Added Proxy:")
    print(f"  ID: {proxy['id']}")
    print(f"  {proxy['proxy']['host']}:{proxy['proxy']['port']}")
    print(f"  Country: {proxy['location']['country']}")

def cmd_export(args):
    ps = create_persona_system(args.data_dir)
    data = ps.export_all_data()
    
    output_file = args.output or "persona_export.json"
    with open(output_file, 'w') as f:
        import json
        json.dump(data, f, indent=2, default=str)
    
    print(f"Exported data to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Persona Identity System CLI")
    parser.add_argument("--data-dir", default="data/persona", help="Data directory")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    gen_parser = subparsers.add_parser("generate", help="Generate identity")
    gen_parser.add_argument("--batch", type=int, help="Generate multiple identities")
    gen_parser.add_argument("--country", default="US", help="Country code")
    gen_parser.add_argument("--gender", choices=["Male", "Female"], help="Gender")
    gen_parser.add_argument("--age-min", type=int, default=22, help="Min age")
    gen_parser.add_argument("--age-max", type=int, default=45, help="Max age")
    
    list_parser = subparsers.add_parser("list", help="List identities")
    
    stats_parser = subparsers.add_parser("stats", help="Show system stats")
    
    acc_parser = subparsers.add_parser("create-account", help="Create account")
    acc_parser.add_argument("--identity-id", help="Identity ID")
    acc_parser.add_argument("--service", required=True, help="Service name")
    acc_parser.add_argument("--email", required=True, help="Email")
    acc_parser.add_argument("--password", required=True, help="Password")
    acc_parser.add_argument("--username", help="Username")
    acc_parser.add_argument("--category", help="Service category")
    
    proxy_parser = subparsers.add_parser("add-proxy", help="Add proxy")
    proxy_parser.add_argument("--host", required=True, help="Proxy host")
    proxy_parser.add_argument("--port", type=int, required=True, help="Proxy port")
    proxy_parser.add_argument("--protocol", default="http", help="Protocol")
    proxy_parser.add_argument("--username", help="Auth username")
    proxy_parser.add_argument("--password", help="Auth password")
    proxy_parser.add_argument("--country", default="US", help="Country")
    
    export_parser = subparsers.add_parser("export", help="Export data")
    export_parser.add_argument("--output", help="Output file")
    
    args = parser.parse_args()
    
    if args.command == "generate":
        cmd_generate(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "stats":
        cmd_stats(args)
    elif args.command == "create-account":
        cmd_create_account(args)
    elif args.command == "add-proxy":
        cmd_add_proxy(args)
    elif args.command == "export":
        cmd_export(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
