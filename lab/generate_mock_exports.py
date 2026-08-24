import json
import zipfile
import time

def create_export(username, followers, following, filename):
    followers_data = {
        "relationships_followers": [
            {
                "string_list_data": [
                    {
                        "href": f"https://www.instagram.com/{user}",
                        "value": user,
                        "timestamp": int(time.time())
                    }
                ]
            }
            for user in followers
        ]
    }

    following_data = {
        "relationships_following": [
            {
                "string_list_data": [
                    {
                        "href": f"https://www.instagram.com/{user}",
                        "value": user,
                        "timestamp": int(time.time())
                    }
                ]
            }
            for user in following
        ]
    }

    with zipfile.ZipFile(filename, 'w') as zf:
        zf.writestr('followers_1.json', json.dumps(followers_data, indent=2))
        zf.writestr('following.json', json.dumps(following_data, indent=2))
        
    print(f"Created {filename}")

if __name__ == "__main__":
    # Mock data for diegodepab
    # follows: yeisonfigueroa.ink, mutual_friend1
    # followers: yeisonfigueroa.ink, mutual_friend1
    diegodepab_followers = ["yeisonfigueroa.ink", "mutual_friend1", "fan_of_diego"]
    diegodepab_following = ["yeisonfigueroa.ink", "mutual_friend1"]
    
    # Mock data for yeisonfigueroa.ink
    # follows: diegodepab, mutual_friend1, tattoo_client1
    # followers: diegodepab, mutual_friend1, tattoo_client1, tattoo_client2
    yeison_followers = ["diegodepab", "mutual_friend1", "tattoo_client1", "tattoo_client2"]
    yeison_following = ["diegodepab", "mutual_friend1", "tattoo_client1"]
    
    create_export("diegodepab", diegodepab_followers, diegodepab_following, "diegodepab_export.zip")
    create_export("yeisonfigueroa.ink", yeison_followers, yeison_following, "yeison_export.zip")

