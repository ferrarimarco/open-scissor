#ifndef _CONFIGMANAGER_HPP_
#define _CONFIGMANAGER_HPP_ 

/**
  * CompositionManager.hpp
  * Singleton directory of the installed compositions.
  * It provides an  entry point both for the python bindings and the c++ interface.
  * It is used in order to create, delete and access the installed compositions.
  */

#include <memory>
#include <algorithm>

#include <Composition.hpp>
#include <PoolManager.hpp>

// Andrea, I don't know what the XML for a composition should look like anymore

using namespace pugi;

namespace bm
{
    class CompositionManager
    {
        /**
          * class constructor
          * private,as in Meyer's singleton
          */
        CompositionManager()
        : m_config_map()
        {}

        ~CompositionManager()
        {}

        /**
          * this object is non-moveable and non-copyable
          */
        CompositionManager(const CompositionManager &) = delete;
        CompositionManager& operator=(const CompositionManager &) = delete;
        CompositionManager(CompositionManager &&) = delete;
        CompositionManager& operator=(CompositionManager &&) = delete;

        std::map<std::string, std::shared_ptr<Composition> > m_config_map;

    public:
        /**
          * unique instance accessor as in Meyer's singleton
          * @return a reference to the only instance of this class
          */
        static CompositionManager& 
        instance()
        {
            static CompositionManager cm;
            return cm;
        }


        /**
          * Exposed by the python bindings.
          * Delete a composition from the directory
          * Notice that external connections among different compositions have to be explicitly deleted.
          * @param name composition name
          */
        void delete_composition(const std::string &name)
        {
            auto it = m_config_map.find(name);
            if(it == m_config_map.end())
                throw std::runtime_error(std::string(name).append(" : composition does not exist"));
            m_config_map.erase(it);
        }

        /**
          * Exposed by the python bindings.
          * Creates an empty composition in the directory.
          * @param name composition name
          */
        void add_composition(const std::string &name)
        {

            std::map<std::string, std::shared_ptr<Composition> >::iterator it;
            it = m_config_map.find(name);
            if(it != m_config_map.end())
                throw std::runtime_error(std::string(name).append(" : composition already exists"));
            m_config_map.insert(std::make_pair( name, std::shared_ptr<Composition>(new Composition(name))));


        }

        /**
          * Exposed by the python bindings.
          * Used to access one of the compositions in the directory.
          * @param composition_id the name of the compositions
          * @return reference to the composition  
          */ 

        Composition& 
        get_composition(const std::string &composition_id)
        {
            auto it = m_config_map.find(composition_id);
            if(it == m_config_map.end())
                throw std::runtime_error("CompositionManager:: composition not found");
            return *(it->second);
        }

        /**
          * Only entry point for the c++ interface
          * It creates a composition in the directory directly from an xml file.
          * @param xmlfile name of the file where the xml describing the composition is contained
          */ 
        void add_config_from_file(const std::string & xmlfile)
        {

            xml_document _M_doc;
            xml_parse_result res = _M_doc.load_file(xmlfile.c_str());
            if (!res) {
                throw std::runtime_error(std::string("init: ").append(res.description()));
            }

            xml_node config = _M_doc.child("composition");
            if(!config)
                throw std::runtime_error("composition node not found");

            std::string composition_id = config.attribute("id").value();
            std::string app_id = config.attribute("app_id").value();


            xml_node install = config.child("install");
            if(install)
            {
                for(xml_node p = install.child("threadpool"); p; p = p.next_sibling("threadpool"))
                    PoolManager::instance().create_pool(p);
                auto it = m_config_map.find(composition_id);
                if(it != m_config_map.end())
                    throw std::runtime_error(composition_id.append(" : composition already exists"));
                auto it2 = m_config_map.insert(std::make_pair(composition_id,std::shared_ptr<Composition>(new Composition(app_id))));
                it2.first->second->install(install);
            }
            else 
            {
                throw std::runtime_error(" only installation is allowed through this entry point");
            }

        }






    };

}//namespace bm

#endif /* _CONFIGMANAGER_HPP_ */
