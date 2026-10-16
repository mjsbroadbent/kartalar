// pois inside a bbox: nodes and (centroids of) ways with amenity/shop/tourism/craft/office tags -> ndjson
#include <osmium/io/pbf_input.hpp>
#include <osmium/handler.hpp>
#include <osmium/visitor.hpp>
#include <osmium/index/map/flex_mem.hpp>
#include <osmium/handler/node_locations_for_ways.hpp>
#include <iostream>
#include <string>
#include <cstdlib>
double X0,Y0,X1,Y1;
const char* KEYS[]={"amenity","shop","tourism","craft","leisure","cuisine","opening_hours","name","name:en","name:ru","name:ky","brand","diet:halal","drink:alcohol","stars","rooms","building","building:levels","takeaway","delivery","outdoor_seating","internet_access","payment:cards",nullptr};
std::string esc(const char*s){std::string o;for(;*s;s++){if(*s=='"'||*s=='\\'){o+='\\';o+=*s;}else if((unsigned char)*s<32)o+=' ';else o+=*s;}return o;}
struct H: osmium::handler::Handler{
 void out(const char*type,long long id,double x,double y,const osmium::TagList&t){
  if(x<X0||x>X1||y<Y0||y>Y1)return;
  if(!t["amenity"]&&!t["shop"]&&!t["tourism"]&&!t["craft"])return;
  std::cout<<"{\"osm\":\""<<type<<id<<"\",\"lon\":"<<x<<",\"lat\":"<<y;
  for(int i=0;KEYS[i];i++){const char*v=t[KEYS[i]]; if(v)std::cout<<",\""<<KEYS[i]<<"\":\""<<esc(v)<<"\"";}
  std::cout<<"}\n";}
 void node(const osmium::Node&n){ if(n.location().valid()) out("n",n.id(),n.location().lon(),n.location().lat(),n.tags()); }
 void way(const osmium::Way&w){ const auto&t=w.tags(); if(!t["amenity"]&&!t["shop"]&&!t["tourism"]&&!t["craft"])return;
  double sx=0,sy=0;int k=0; for(auto&nr:w.nodes()){ if(nr.location().valid()){sx+=nr.location().lon();sy+=nr.location().lat();k++;}}
  if(k) out("w",w.id(),sx/k,sy/k,t); }
};
int main(int c,char**v){ X0=atof(v[2]);Y0=atof(v[3]);X1=atof(v[4]);Y1=atof(v[5]); std::cout.precision(8);
 using Idx=osmium::index::map::FlexMem<osmium::unsigned_object_id_type,osmium::Location>; Idx idx; osmium::handler::NodeLocationsForWays<Idx> loc{idx};
 osmium::io::Reader r{v[1],osmium::osm_entity_bits::node|osmium::osm_entity_bits::way}; H h; osmium::apply(r,loc,h); r.close(); }
